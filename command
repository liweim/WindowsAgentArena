sudo npm install -g @openai/codex@latest

给权限：sudo chmod -R a+rwX /home/weimingli/projects/WindowsAgentArena

cd /home/weimingli/projects/LocalLSTC/benchmarks/WindowsAgentArena/scripts
build win11: ./run-local.sh --prepare-image true (监听：http://localhost:3380/，日志：/shared/ps_script_log.txt和/shared/server.log)
手动启动服务：& "C:\Users\Docker\AppData\Local\Programs\Python\Python310\python.exe" "C:\oem\server\main.py" --port 5000
手动更新软件并关闭保存：./run.sh --mode dev --prepare-image false --skip-build true --start-client false --container-name a11yarena-lwm --browser-port 9005 --rdp-port 3370 （每个软件都打开一下，xlsx需要新建一个然后保存成xlsx格式）
build env: ./build-container-image.sh --mode dev --image-tag locallstc-stable
bash run_win.sh

人工验证：
conda activate winarena
cd /home/weimingli/projects/WindowsAgentArena/scripts
python run_human.py \
    --example /home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client/evaluation_examples_windows/examples/hearing/service-cms\_update\_voyage\_stock\_audio.json \
    --container-name winarena-human \
    --browser-port 9016 \
    --rdp-port 3400

起服务：
nohup python -m vllm.entrypoints.openai.api_server \
    --served-model-name qwen3.8-27b \
    --model /home/weimingli/models/Qwen3.8-27B \
    --gpu-memory-utilization 0.9 \
    --max-model-len 131072 \
    --max-num-seqs 10 \
    --reasoning-parser qwen3 \
    --host 0.0.0.0 \
    --port 30000 \
    > qwen.log 2>&1 &

语音识别：
PARAKEET_DEVICE=auto nohup python -m uvicorn \
  mm_agents.parakeet_asr.server:app \
  --app-dir /home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client \
  --host 0.0.0.0 --port 18765 --workers 1 \
  > /home/weimingli/projects/WindowsAgentArena/parakeet-asr.log 2>&1 &

跑框架：cd scripts & ./run_locallstc.sh
杀进程：./stop_run.sh a11yarena-locallstc
看结果：watch -n 60 python -m src.win-arena-container.client.mm_agents.utils

git部分添加：git -C /home/weimingli/projects/WindowsAgentArena add -A -- . ':(exclude)src/win-arena-container/client/evaluation_examples_windows/examples/motor/**' ':(exclude)src/win-arena-container/client/evaluation_examples_windows/examples/visual/**'

ssh -N -L 13400:127.0.0.1:3400 -L 19005:127.0.0.1:9005 weimingli@129.94.175.253