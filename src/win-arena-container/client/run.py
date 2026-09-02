"""Script to run end-to-end evaluation on the benchmark.
Utils and basic architecture credit to https://github.com/web-arena-x/webarena/blob/main/run.py.
"""
import datetime
import json
import logging
import os
import sys
import shutil
import subprocess
import traceback
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
# import wandb

from tqdm import tqdm

import lib_run_single
from desktop_env.envs.desktop_env import DesktopEnv
from mm_agents.compat import (
    FRAMEWORK_AGENT_NAMES,
    STEP_AGENT_NAMES,
    build_step_agent,
    run_framework_example,
    run_step_agent_example,
)
from mm_agents.cli import parse_agent_args
from mm_agents.navi.agent import NaviAgent
import requests
import time

from threading import Event
import signal

print("Waiting for the server to start...")

#  Logger Configs {{{ #
def _resolve_log_timezone():
    tz_name = os.environ.get("LOCALLSTC_LOG_TZ") or os.environ.get("TZ") or "Australia/Sydney"
    if ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    return datetime.datetime.now().astimezone().tzinfo


LOG_TZ = _resolve_log_timezone()


def _log_now() -> datetime.datetime:
    return datetime.datetime.now(LOG_TZ)


class LocalTimezoneFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.datetime.fromtimestamp(record.created, LOG_TZ)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]


root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.propagate = True
datetime_str: str = _log_now().strftime("%Y%m%d@%H%M%S")
formatter = LocalTimezoneFormatter(
    fmt="\x1b[1;33m[%(asctime)s \x1b[31m%(levelname)s \x1b[32m%(module)s/%(lineno)d-%(processName)s\x1b[1;33m] \x1b[0m%(message)s")
for noisy_logger_name in ("openai", "openai._base_client", "httpx", "httpcore"):
    logging.getLogger(noisy_logger_name).setLevel(logging.WARNING)

def setup_logging(args):
    logging_dir: str = os.path.join(
        args.result_dir, 
        "logs"
    )
    
    os.makedirs(logging_dir, exist_ok=True)

    file_handler = logging.FileHandler(os.path.join(logging_dir, "normal-{}-{}.log".format(args.worker_id, datetime_str)), encoding="utf-8")
    debug_handler = logging.FileHandler(os.path.join(logging_dir, "debug-{}-{}.log".format(args.worker_id, datetime_str)), encoding="utf-8")
    stdout_handler = logging.StreamHandler(sys.stdout)
    sdebug_handler = logging.FileHandler(os.path.join(logging_dir, "sdebug-{}-{}.log".format(args.worker_id, datetime_str)), encoding="utf-8")

    file_handler.setLevel(logging.INFO)
    debug_handler.setLevel(logging.DEBUG)
    stdout_handler.setLevel(logging.INFO)
    sdebug_handler.setLevel(logging.DEBUG)

    file_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    stdout_handler.setFormatter(formatter)
    sdebug_handler.setFormatter(formatter)

    stdout_handler.addFilter(logging.Filter("desktopenv"))
    sdebug_handler.addFilter(logging.Filter("desktopenv"))

    root_logger.addHandler(file_handler)
    root_logger.addHandler(debug_handler)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(sdebug_handler)
#  }}} Logger Configs # 

logger = logging.getLogger("desktopenv.experiment")
CONTAINER_RESTART_EXIT_CODE = 75

def config():
    """Delegate the untouched process command line to the selected method."""
    return parse_agent_args()


def clean_result_directory(result_dir):
    """Clear one explicit result directory after method-level validation."""
    target = os.path.realpath(os.path.abspath(result_dir))
    current = os.path.realpath(os.getcwd())
    protected = {os.path.realpath(os.sep), os.path.realpath("/client")}
    if target in protected or current == target or current.startswith(target + os.sep):
        raise ValueError("Refusing to clean protected result directory: {}".format(target))
    os.makedirs(target, exist_ok=True)
    for name in os.listdir(target):
        path = os.path.join(target, name)
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)

def test(
        args,
        test_all_meta: dict
) -> None:
    scores = []
    max_steps = args.max_steps

    # log args
    logger.info("Args: %s", args)
    # set wandb project
    cfg_args = \
    {
        "headless": args.headless,
        "action_space": args.action_space,
        "observation_type": args.observation_type,
        "screen_width": args.screen_width,
        "screen_height": args.screen_height,
        "sleep_after_execution": args.sleep_after_execution,
        "max_steps": args.max_steps,
        "a11y_backend": args.a11y_backend,
        "max_trajectory_length": args.max_trajectory_length,
        "agent_name": args.agent_name,
        "som_origin": args.som_origin,
        "model": args.model,
        "temperature": args.temperature,
        "seed": args.seed,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "max_tokens": args.max_tokens,
        "stop_token": args.stop_token,
        "result_dir": args.result_dir,
        "trial_id": args.trial_id,
        "worker_id": args.worker_id,
        "num_workers": args.num_workers,
    }

    if cfg_args["agent_name"] in FRAMEWORK_AGENT_NAMES | STEP_AGENT_NAMES:
        agent = None
    elif cfg_args["agent_name"] == "navi":
        if cfg_args["som_origin"] in ["a11y", "omni", "mixed-omni"]:
            som_config = None
        elif cfg_args["som_origin"] in ["oss", "mixed-oss"]:
            som_config = {
                "pipeline": ["webparse", "groundingdino", "ocr"],
                "groundingdino": {
                    "prompts": ["icon", "image"]
                },
                "ocr": {
                    "class_name": "TesseractOCR"
                },
                "webparse": {
                    "cdp_url": f"http://{args.emulator_ip}:9222"
                }
            }
        
        agent = NaviAgent(
            server="oai",
            model=args.model,
            som_config=som_config,
            som_origin=args.som_origin,
            temperature=args.temperature
        )
    elif cfg_args["agent_name"] == "claude":
        from mm_agents.claude.agent import ClaudeAgent
        agent = ClaudeAgent()
    else:
        raise ValueError(f"Unknown agent name: {cfg_args['agent_name']}")
    
    env = DesktopEnv(
        action_space=(agent.action_space if agent is not None else args.action_space),
        screen_size=(args.screen_width, args.screen_height),
        headless=args.headless,
        require_a11y_tree=args.observation_type in ["a11y_tree", "screenshot_a11y_tree", "som"],
        emulator_ip=args.emulator_ip, #for OS running on docker
        a11y_backend=args.a11y_backend
    )
    if cfg_args["agent_name"] in STEP_AGENT_NAMES:
        agent = build_step_agent(args, env)

    for domain in tqdm(test_all_meta, desc="Domain"):
        for example_id in tqdm(test_all_meta[domain], desc="Example", leave=False):
            if not ensure_server_ready_or_restart(args.emulator_ip):
                logger.error("VM server is unavailable and automatic restart failed; stopping remaining tasks.")
                env.close()
                raise SystemExit(CONTAINER_RESTART_EXIT_CODE)

            if args.diff_lvl == "normal":
                logger.info(f"Windows Agent Arena: Starting on NORMAL difficulty")
                config_file = os.path.join(args.test_config_base_dir, f"examples/{domain}/{example_id}.json")
                logger.info(f"\nTESTING ON TASK CONFIG PATH: {config_file}")

            elif args.diff_lvl == "hard":
                logger.info(f"Windows Agent Arena: Starting on HARDER difficulty")
                
                config_file = os.path.join(args.test_config_base_dir, f"examples_noctxt/{domain}/{example_id}.json")
                logger.info(f"\nTESTING ON TASK CONFIG PATH: {config_file}")

            else:
                sys.exit("Invalid value for arg --diff_lvl. Choose 'normal' or 'hard'.")

            with open(config_file, "r", encoding="utf-8") as f:
                example = json.load(f)
            example["__task_config_path"] = os.path.abspath(config_file)
            example["domain"] = domain

            logger.info(f"[Domain]: {domain}")
            logger.info(f"[Example ID]: {example_id}")

            instruction = example["instruction"]

            logger.info(f"[Instruction]: {instruction}")
            # wandb each example config settings
            cfg_args["instruction"] = instruction
            cfg_args["start_time"] = _log_now().strftime("%Y:%m:%d-%H:%M:%S")
            # run.config.update(cfg_args)

            example_result_dir = os.path.join(
                args.result_dir,
                domain,
                example_id
            )
            os.makedirs(example_result_dir, exist_ok=True)
            
            # Example Logging Config {{{
            os.makedirs(os.path.join(example_result_dir, "logs"), exist_ok=True)
            task_log_handler = logging.FileHandler(os.path.join(example_result_dir, "logs", "task-{}-{}.log".format(args.worker_id, datetime_str)), encoding="utf-8")
            task_log_handler.setLevel(logging.DEBUG)
            task_log_handler.setFormatter(formatter)
            root_logger.addHandler(task_log_handler)
            # }}} Example Logging Config
            
            # example start running
            try:
                if cfg_args["agent_name"] in FRAMEWORK_AGENT_NAMES:
                    score = run_framework_example(
                        env, example, args, example_result_dir, scores
                    )
                elif cfg_args["agent_name"] in STEP_AGENT_NAMES:
                    score = run_step_agent_example(
                        agent, env, example, args, example_result_dir, scores
                    )
                else:
                    lib_run_single.run_single_example(
                        agent,
                        env,
                        example,
                        max_steps,
                        instruction,
                        args,
                        example_result_dir,
                        scores,
                    )
                    score = scores[-1] if scores else 0.0
            except Exception as e:
                logger.error(f"Exception in {domain}/{example_id}: {e}")
                error_traceback = traceback.format_exc()
                logger.error(error_traceback)
                # env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))
                # Write error details to traj.jsonl
                with open(os.path.join(example_result_dir, "traj.jsonl"), "a") as f:
                    f.write(json.dumps({
                        "Error": f"Exception in {domain}/{example_id}",
                        "Exception": str(e),
                        "Traceback": error_traceback,
                    }))
                    f.write("\n")
                
                # Write error details with stack trace to traj.html
                with open(os.path.join(example_result_dir, "traj.html"), "a") as f:
                    f.write(f"<h1>Error: Exception in {domain}/{example_id}</h1>")
                    f.write(f"<p>{e}</p>")
                    f.write("<pre>")
                    f.write(error_traceback)
                    f.write("</pre>")
            else:
                logger.info(f"Finished {domain}/{example_id} score={score}")
            finally:
                # Cleanup task log handler
                root_logger.removeHandler(task_log_handler)
                task_log_handler.close()

    env.close()
    # logger.info(f"UPDATED SCORES: {scores}")
        
    if len(scores) == 0:
        logger.info("No examples finished.")
    else:
        logger.info(f"Average score: {sum(scores) / len(scores)}")


def _clear_task_result_dir(example_path):
    if not os.path.isdir(example_path):
        return
    for file in os.listdir(example_path):
        out_path = os.path.join(example_path, file)
        if os.path.isdir(out_path):
            shutil.rmtree(out_path)
        else:
            os.remove(out_path)


def get_unfinished(action_space, use_model, observation_type, result_dir, trial_id, total_file_json, rerun=False, rerun_fail=False):
    if not os.path.exists(result_dir):
        return total_file_json

    tasks_to_run = {}
    for domain, example_ids in total_file_json.items():
        tasks_to_run[domain] = []
        for example_id in example_ids:
            example_path = os.path.join(result_dir, domain, example_id)
            result_path = os.path.join(example_path, "result.txt")
            err_reason_path = os.path.join(example_path, "err_reason.txt")
            has_error = os.path.exists(err_reason_path)
            if rerun and os.path.exists(result_path):
                os.remove(result_path)

            if os.path.isdir(example_path) and (has_error or not os.path.exists(result_path)):
                if has_error:
                    logger.info("Rerunning %s/%s because err_reason.txt exists", domain, example_id)
                _clear_task_result_dir(example_path)
                result_path = os.path.join(example_path, "result.txt")
                err_reason_path = os.path.join(example_path, "err_reason.txt")

            should_skip = False
            if not rerun and os.path.exists(result_path) and not os.path.exists(err_reason_path):
                try:
                    result = float(open(result_path, "r").read().strip())
                    if result <= 0.0 and rerun_fail:
                        os.remove(result_path)
                    if result > 0.0 or not rerun_fail:
                        should_skip = True
                except (ValueError, IOError) as e:
                    logger.warning("Failed to read result for %s/%s: %s", domain, example_id, e)

            if not should_skip:
                tasks_to_run[domain].append(example_id)

    return tasks_to_run


def get_result(action_space, use_model, observation_type, result_dir, trial_id, total_file_json):
    target_dir = result_dir
    if not os.path.exists(target_dir):
        print("New experiment, no result yet.")
        return None

    all_result = []

    for domain in os.listdir(target_dir):
        domain_path = os.path.join(target_dir, domain)
        if os.path.isdir(domain_path):
            for example_id in os.listdir(domain_path):
                example_path = os.path.join(domain_path, example_id)
                if os.path.isdir(example_path):
                    if "result.txt" in os.listdir(example_path):
                        # empty all files under example_id
                        try:
                            all_result.append(float(open(os.path.join(example_path, "result.txt"), "r").read()))
                        except:
                            all_result.append(0.0)

    if not all_result:
        print("New experiment, no result yet.")
        return None
    else:
        print("Current Success Rate:", sum(all_result) / len(all_result) * 100, "%")
        return all_result


exit_event = Event()
def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit_event.set()
    exit(0)

    
def probe_server(ip, port=5000, timeout=7):
    try:
        response = requests.get("http://" + ip + ":" + str(port) + "/probe", timeout=timeout)
        if response.status_code == 200:
            return True
        logger.warning("VM probe returned status %s", response.status_code)
    except Exception as e:
        logger.warning("VM probe failed: %s", e)
    return False


def wait_for_server(ip, port=5000):
    while not exit_event.is_set():
        if probe_server(ip, port):
            print("Server is ready")
            return True
        print("Retrying...")
        exit_event.wait(5)
    return False


def _log_command_output(label, command, timeout=10):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = result.stdout.strip()
        logger.error("%s rc=%s\n%s", label, result.returncode, output or "<empty>")
    except Exception as e:
        logger.error("%s failed: %s", label, e)


def _log_file_tail(label, path, lines=120):
    if not os.path.exists(path):
        logger.error("%s missing: %s", label, path)
        return
    _log_command_output(label, ["tail", "-n", str(lines), path])


def log_vm_diagnostics(restart_log_path):
    logger.error("Collecting WinArena VM diagnostics after server recovery failure")
    _log_command_output("qemu processes", ["pgrep", "-af", "qemu-system"])
    _log_command_output("qemu pid file", ["bash", "-lc", "ls -l /run/shm/qemu.* 2>&1 || true"])
    _log_file_tail("qemu log", "/run/shm/qemu.log")
    _log_file_tail("qemu stdout", "/run/shm/qemu.out")
    _log_file_tail("qemu terminal", "/run/shm/qemu.pty")
    _log_file_tail("entry setup restart log", restart_log_path)
    _log_file_tail("windows power config log", "/shared/power_config_log.txt")


def restart_vm_server(ip, port=5000, timeout=300):
    logger.warning("VM server %s:%s is not reachable; restarting the WinArena VM", ip, port)
    restart_log_path = "/tmp/winarena-entry-setup-restart.log"
    # Do not use `pkill -f qemu-system` from a shell whose command line also
    # contains that pattern: pkill can kill the restart shell itself before it
    # reaches entry_setup.sh. Anchor the match at the start of QEMU's command
    # line so it cannot match this Python process, then launch the setup script
    # as a separate process.
    subprocess.run(["pkill", "-f", "^qemu-system-x86_64( |$)"], check=False)
    time.sleep(3)
    with open(restart_log_path, "ab") as restart_log:
        subprocess.Popen(["/entry_setup.sh"], stdout=restart_log, stderr=subprocess.STDOUT)

    deadline = time.time() + timeout
    while time.time() < deadline and not exit_event.is_set():
        if probe_server(ip, port):
            logger.warning("VM server recovered after restart")
            return True
        time.sleep(5)

    logger.error("VM server did not recover within %s seconds; restart log: %s", timeout, restart_log_path)
    log_vm_diagnostics(restart_log_path)
    return False


def ensure_server_ready_or_restart(ip, port=5000):
    if probe_server(ip, port):
        return True
    return restart_vm_server(ip, port)

# Handling keyboard interrupts
for sig in ('TERM', 'HUP', 'INT'):
    signal.signal(getattr(signal, 'SIG'+sig), quit)

if __name__ == '__main__':
    ####### The complete version of the list of examples #######
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    args = config()
    if args.clean_results and not getattr(args, "get_score", False):
        clean_result_directory(args.result_dir)
    setup_logging(args)

    if getattr(args, "get_score", False):
        get_result(
            args.action_space,
            args.model,
            args.observation_type,
            args.result_dir,
            args.trial_id,
        )
        raise SystemExit(0)

    wait_for_server(args.emulator_ip)

    with open(args.test_all_meta_path, "r", encoding="utf-8") as f:
        test_all_meta = json.load(f)

    logger.info(f"\nTESTING ON TASK JSON PATH: {args.test_all_meta_path}")

    if args.domain != "all":
        test_all_meta = {args.domain: test_all_meta[args.domain]}
    
    if args.num_workers == 1:
        test_file_list = get_unfinished(
            args.action_space,
            args.model,
            args.observation_type,
            args.result_dir,
            args.trial_id,
            test_all_meta,
            args.rerun,
            args.rerun_fail
        )
    else:
        # if we have more than one worker (Azure runs) then we distribute the tasks equally
        # otherwise they will try to delete each other's partial results in get_unfinished
        test_file_list = test_all_meta

    left_info = ""
    for domain in test_file_list:
        left_info += f"{domain}: {len(test_file_list[domain])}\n"
    logger.info(f"Left tasks:\n{left_info}")

    # distribute tasks among workers
        # Flatten your dict into a list of tasks  
    all_tasks_test  = [(domain, example_id) for domain in test_file_list for example_id in test_file_list[domain]]  

    # Calculate the start and end indices of the tasks for this worker    
    tasks_per_worker = len(all_tasks_test) // args.num_workers    
    extra = len(all_tasks_test) % args.num_workers  # calculate the number of tasks that can't be evenly distributed  
    
    start_index = args.worker_id * tasks_per_worker + min(args.worker_id, extra)  
    if args.worker_id < extra:  
        end_index = start_index + tasks_per_worker + 1  
    else:  
        end_index = start_index + tasks_per_worker  
    
    # Slice the tasks for this worker  
    tasks_for_this_worker = all_tasks_test[start_index:end_index]

    # log which tasks this worker is doing
    logger.info(f"Worker {args.worker_id} is doing tasks: {tasks_for_this_worker}")
  
    # Convert the list of tasks back to a dictionary  
    test_file_list_worker = {}  
    for domain, example_id in tasks_for_this_worker:  
        if domain not in test_file_list_worker: 
            # create an empty list to which elements will be appended 
            test_file_list_worker[domain] = []  
        test_file_list_worker[domain].append(example_id)  

    get_result(args.action_space,
        args.model,
        args.observation_type,
        args.result_dir,
        args.trial_id,
        test_file_list_worker
    )
    test(args, test_file_list_worker)
