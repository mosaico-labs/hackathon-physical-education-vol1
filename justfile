# hackathon-physical-education-vol1 — run `just` to see every command. See README.md.

set dotenv-load
set shell := ["bash", "-euo", "pipefail", "-c"]

# install exactly what uv.lock says (the laptop has no Mosaico SDK checkout to re-resolve against)
export UV_FROZEN := "1"
# never contact the Hugging Face Hub: datasets and models stay on this computer
export HF_HUB_OFFLINE := "1"

team := env("TEAM", "")
data_dir := env("DATA_DIR", "data")
cloud := env("CLOUD_HOST", "hackathon")
cloud_dir := env("CLOUD_DIR", "hackathon-physical-education-vol1")
mosaico_host := env("MOSAICO_HOST", "mosaico.hackathon.internal")
mosaico_port := env("MOSAICO_PORT", "6726")
sdk_path := env("MOSAICO_SDK_PATH", "/home/ubuntu/workspace/mosaico/mosaico-sdk-py")
device := env("DEVICE", if os() == "macos" { "mps" } else { "cuda" })
cameras := env("CAMERAS", "{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30} }")
_robot := "--robot.type=so101_follower --robot.port=" + env("FOLLOWER_PORT", "/dev/ttyACM0") + " --robot.id=" + env("FOLLOWER_ID", "follower")
_teleop := "--teleop.type=so101_leader --teleop.port=" + env("LEADER_PORT", "/dev/ttyACM1") + " --teleop.id=" + env("LEADER_ID", "leader")
_cams := "--robot.cameras=" + quote(cameras)
# LeRobot wants a dataset id; "local/<name>" is just a label, the data lives in data/<name>
_repo := "--dataset.repo_id=local/"

default:
    @just --list --unsorted

# ============================================================== setup ==

# set up this repo on your laptop
[group('setup')]
local-setup: _env
    uv sync

# set up this repo on the cloud machine (also installs the Mosaico SDK)
[group('setup')]
cloud-setup: _env
    test -f "{{ sdk_path }}/pyproject.toml" || (echo "Mosaico SDK not found at {{ sdk_path }}: set MOSAICO_SDK_PATH in .env" && exit 1)
    ln -sfn "{{ sdk_path }}" vendor/mosaico-sdk-py
    uv sync --group cloud

_env:
    @test -f .env || (cp .env.example .env && echo "Created .env: open it and fill it in.")

# ============================================================== local ==

# find the USB port of each arm
[group('local')]
find-port:
    uv run lerobot-find-port

# list the connected cameras
[group('local')]
find-cameras:
    uv run lerobot-find-cameras opencv

# give the motors their ids (new arms only): just setup-motors follower|leader
[group('local')]
setup-motors who="follower":
    uv run lerobot-setup-motors {{ if who == "leader" { _teleop } else { _robot } }}

# calibrate an arm: just calibrate follower|leader
[group('local')]
calibrate who="follower":
    uv run lerobot-calibrate {{ if who == "leader" { _teleop } else { _robot } }}

# move the follower with the leader arm
[group('local')]
teleop:
    uv run lerobot-teleoperate {{ _robot }} {{ _teleop }} {{ _cams }} --display_data=true

# record episodes into data/<name>: just record pick "Pick up the red cube" 10
[group('local')]
record name task episodes="10" *args:
    uv run lerobot-record {{ _robot }} {{ _teleop }} {{ _cams }} --display_data=true \
        {{ _repo }}{{ name }} --dataset.root="{{ data_dir }}/{{ name }}" \
        --dataset.single_task={{ quote(task) }} --dataset.num_episodes={{ episodes }} \
        --dataset.video=false --dataset.no_stamp=true --dataset.push_to_hub=false {{ args }}

# watch an episode of data/<name>
[group('local')]
viz name episode="0":
    uv run lerobot-dataset-viz --repo-id local/{{ name }} --root "{{ data_dir }}/{{ name }}" --episode-index {{ episode }}

# copy data/<name> to the cloud machine
[group('local')]
upload name:
    uv run starter check "{{ data_dir }}/{{ name }}"
    rsync -az --progress "{{ data_dir }}/{{ name }}" "{{ cloud }}:{{ cloud_dir }}/{{ data_dir }}/"

# copy a folder from the cloud machine into outputs/pulled/: just pull outputs/train/pick_act
[group('local')]
pull path:
    mkdir -p outputs/pulled
    rsync -az --progress "{{ cloud }}:{{ cloud_dir }}/{{ path }}" outputs/pulled/

# run a trained policy on the arm: just rollout outputs/pulled/pick_act "Pick up the red cube"
[group('local')]
rollout run task:
    uv run lerobot-rollout --strategy.type=base {{ _robot }} {{ _cams }} \
        --policy.path="{{ run }}/checkpoints/last/pretrained_model" --task={{ quote(task) }}

# ============================================================== cloud ==

# check the connection to Mosaico
[group('cloud')]
ping:
    uv run starter ping

# send data/<name> to Mosaico as <TEAM>_<name>_episode_NNNNNN
[group('cloud')]
push name *args:
    @test -n "{{ team }}" -a "{{ team }}" != "change-me" || (echo "Set TEAM in .env first." && exit 1)
    uv run starter check "{{ data_dir }}/{{ name }}"
    uv run mosaicolabs.lerobot_injector "{{ data_dir }}/{{ name }}" --name "{{ team }}_{{ name }}" \
        --metadata {{ quote('{"team": "' + team + '", "dataset": "' + name + '"}') }} \
        --host {{ mosaico_host }} --port {{ mosaico_port }} {{ args }}

# list the sequences in Mosaico: just sequences --name 'team-07_*' --task 'Pick*'
[group('cloud')]
sequences *args:
    uv run starter sequences {{ args }}

# rebuild a dataset in data/<name> from Mosaico: just extract picks --task 'Pick*'
[group('cloud')]
extract name *filters:
    uv run starter extract "{{ data_dir }}/{{ name }}" {{ filters }}

# train a policy on data/<name>, saved in outputs/train/<name>_<policy>: just train pick act 20000
[group('cloud')]
train name policy="act" steps="20000" *args:
    uv run lerobot-train {{ _repo }}{{ name }} --dataset.root="{{ data_dir }}/{{ name }}" \
        --policy.type={{ policy }} --policy.device={{ device }} --policy.push_to_hub=false \
        --steps={{ steps }} --output_dir=outputs/train/{{ name }}_{{ policy }} {{ args }}
