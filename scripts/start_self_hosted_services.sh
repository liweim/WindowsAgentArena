#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PROJECTS_DIR="$(cd -- "${PROJECT_DIR}/.." && pwd)"

DOCKER_ASSETS_DIR="${DOCKER_ASSETS_DIR:-${HOME}/docker-images}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-180}"
CAPTCHA_PORT="${CAPTCHA_PORT:-8765}"

SHOPPING_IMAGE="shopping_final_0712"
SHOPPING_ADMIN_IMAGE="shopping_admin_final_0719"
WIKIPEDIA_IMAGE="ghcr.io/kiwix/kiwix-serve:3.3.0"
FORUM_IMAGE="postmill-populated-exposed-withimg"
WIKIPEDIA_ZIM="wikipedia_en_all_maxi_2022-05.zim"

log() {
  printf '[self-hosted] %s\n' "$*"
}

die() {
  printf '[self-hosted] ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

container_exists() {
  docker container inspect "$1" >/dev/null 2>&1
}

container_is_running() {
  [[ "$(docker container inspect --format '{{.State.Running}}' "$1" 2>/dev/null)" == "true" ]]
}

start_existing_container() {
  local container_name="$1"

  if container_is_running "${container_name}"; then
    log "Container ${container_name} is already running."
  else
    log "Starting existing container ${container_name}..."
    docker start "${container_name}" >/dev/null
  fi
}

ensure_image_from_tar() {
  local image_name="$1"
  local tar_path="$2"

  if docker image inspect "${image_name}" >/dev/null 2>&1; then
    return
  fi

  [[ -f "${tar_path}" ]] || die "Image ${image_name} is missing and tar file was not found: ${tar_path}"
  log "Loading image ${image_name} from ${tar_path} (this can take a while)..."
  docker load --input "${tar_path}"
  docker image inspect "${image_name}" >/dev/null 2>&1 || \
    die "The tar was loaded, but image ${image_name} is still unavailable."
}

ensure_remote_image() {
  local image_name="$1"

  if ! docker image inspect "${image_name}" >/dev/null 2>&1; then
    log "Pulling image ${image_name}..."
    docker pull "${image_name}"
  fi
}

wait_for_command() {
  local description="$1"
  shift
  local started_at
  local last_output=""

  started_at="$(date +%s)"
  log "Waiting for ${description}..."
  while true; do
    if last_output="$("$@" 2>&1)"; then
      log "${description} is ready."
      return 0
    fi

    if (( $(date +%s) - started_at >= STARTUP_TIMEOUT )); then
      printf '%s\n' "${last_output}" >&2
      die "Timed out after ${STARTUP_TIMEOUT}s waiting for ${description}."
    fi
    sleep 5
  done
}

configure_magento() {
  local container_name="$1"
  local port="$2"

  wait_for_command "MySQL in ${container_name}" \
    docker exec "${container_name}" mysql \
      -umagentouser -pMyPassword magentodb -e 'SELECT 1;'

  log "Configuring Magento base URL in ${container_name}..."
  docker exec "${container_name}" \
    /var/www/magento2/bin/magento setup:store-config:set \
    --base-url="http://localhost:${port}"
  docker exec "${container_name}" mysql \
    -umagentouser -pMyPassword magentodb -e \
    "UPDATE core_config_data SET value='http://localhost:${port}/' WHERE path='web/secure/base_url';"
  docker exec "${container_name}" \
    /var/www/magento2/bin/magento cache:flush
}

start_shopping() {
  if container_exists shopping; then
    start_existing_container shopping
  else
    ensure_image_from_tar "${SHOPPING_IMAGE}" \
      "${DOCKER_ASSETS_DIR}/shopping_final_0712.tar"
    log "Creating shopping container..."
    docker run --name shopping -p 7770:80 -p 13306:3306 \
      -d "${SHOPPING_IMAGE}" >/dev/null
  fi

  configure_magento shopping 7770
  log "Allowing WinArena to reset the OneStopShop cart database..."
  docker exec shopping mysql -uroot -p1234567890 -e \
    "GRANT ALL ON magentodb.* TO 'magentouser'@'%' IDENTIFIED BY 'MyPassword'; FLUSH PRIVILEGES;"
}

start_shopping_admin() {
  if container_exists shopping_admin; then
    start_existing_container shopping_admin
  else
    ensure_image_from_tar "${SHOPPING_ADMIN_IMAGE}" \
      "${DOCKER_ASSETS_DIR}/shopping_admin_final_0719.tar"
    log "Creating shopping_admin container..."
    docker run --name shopping_admin -p 7780:80 \
      -d "${SHOPPING_ADMIN_IMAGE}" >/dev/null
  fi

  configure_magento shopping_admin 7780
}

start_wikipedia() {
  if container_exists wikipedia; then
    start_existing_container wikipedia
  else
    [[ -f "${DOCKER_ASSETS_DIR}/${WIKIPEDIA_ZIM}" ]] || \
      die "Wikipedia ZIM file not found: ${DOCKER_ASSETS_DIR}/${WIKIPEDIA_ZIM}"
    ensure_remote_image "${WIKIPEDIA_IMAGE}"
    log "Creating wikipedia container..."
    docker run --name wikipedia \
      --volume "${DOCKER_ASSETS_DIR}:/data:ro" \
      -p 8888:80 -d "${WIKIPEDIA_IMAGE}" "${WIKIPEDIA_ZIM}" >/dev/null
  fi
}

start_forum() {
  if container_exists forum; then
    start_existing_container forum
  else
    ensure_image_from_tar "${FORUM_IMAGE}" \
      "${DOCKER_ASSETS_DIR}/postmill-populated-exposed-withimg.tar"
    log "Creating forum container..."
    docker run --name forum -p 9999:80 -d "${FORUM_IMAGE}" >/dev/null
  fi
}

find_captcha_script() {
  local candidate

  if [[ -n "${CAPTCHA_SCRIPT:-}" ]]; then
    [[ -f "${CAPTCHA_SCRIPT}" ]] || die "CAPTCHA_SCRIPT does not exist: ${CAPTCHA_SCRIPT}"
    printf '%s\n' "${CAPTCHA_SCRIPT}"
    return
  fi

  for candidate in \
    "${DOCKER_ASSETS_DIR}/scripts/run_captcha_service.sh" \
    "${SCRIPT_DIR}/run_captcha_service.sh" \
    "${PROJECTS_DIR}/WindowsAgentArena/scripts/run_captcha_service.sh"
  do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return
    fi
  done

  die "Could not find run_captcha_service.sh; set CAPTCHA_SCRIPT to its path."
}

start_captcha() {
  local captcha_script

  if pgrep -f "[c]aptcha_service.py.*--port[= ]${CAPTCHA_PORT}" >/dev/null 2>&1; then
    log "CAPTCHA service is already running on port ${CAPTCHA_PORT}."
    return
  fi

  captcha_script="$(find_captcha_script)"
  log "Starting CAPTCHA service with ${captcha_script}..."
  (
    cd -- "$(dirname -- "${captcha_script}")"
    bash "${captcha_script}"
  )

  wait_for_command "CAPTCHA service on port ${CAPTCHA_PORT}" \
    pgrep -f "[c]aptcha_service.py.*--port[= ]${CAPTCHA_PORT}"
}

main() {
  require_command docker
  require_command pgrep
  [[ "${STARTUP_TIMEOUT}" =~ ^[0-9]+$ ]] || die "STARTUP_TIMEOUT must be an integer."
  [[ -d "${DOCKER_ASSETS_DIR}" ]] || die "Docker assets directory not found: ${DOCKER_ASSETS_DIR}"
  docker info >/dev/null 2>&1 || die "Docker daemon is not available for the current user."

  start_shopping
  start_shopping_admin
  start_wikipedia
  start_forum
  start_captcha

  log "All self-hosted services are running:"
  printf '  Shopping:       http://localhost:7770/\n'
  printf '  Shopping admin: http://localhost:7780/admin (admin / admin1234)\n'
  printf '  Wikipedia:      http://localhost:8888/%s/A/User:The_other_Kiwix_guy/Landing\n' "${WIKIPEDIA_ZIM%.zim}"
  printf '  Reddit:         http://localhost:9999/\n'
  printf '  CAPTCHA:        http://localhost:%s/\n' "${CAPTCHA_PORT}"
}

main "$@"
