#!/bin/bash
export BRANCH_ID=${BRANCH_ID:-main}
export PLATFORM_ID="RUNPOD"
export TORCH_FORCE_WEIGHTS_ONLY_LOAD=1

export PORT=8000
export HOST="0.0.0.0"
export UI_TYPE="FORGE"
export PROGRAM_PATH=${PROGRAM_PATH:-"/notebooks/stable-diffusion-webui-forge/"}
export RESOURCE_PATH=${RESOURCE_PATH:-"/notebooks/my-runpod-volume/models"}
export LOG_PATH=${LOG_PATH:-"/notebooks/backend.log"}
export PROGRAM_LOG=${PROGRAM_LOG:-"/notebooks/forge.log"}
export JUPYTER_LAB_PORT=${JUPYTER_LAB_PORT:-"8888"}
export OUTPUT_PATH=${OUTPUT_PATH:-"/notebooks/outputs"}

export CMD=${CMD:-"python autolaunch_forge.py"}

start_nginx() {
    echo "Start NGINX"
    service nginx start
}

update_backend() {
    cd /notebooks/program/vjumpkung-sd-ui-manager-backend/ && git pull --ff-only
}

start_backend() {
    echo "Starting Resource Manager WebUI..."
    cd /notebooks/program/vjumpkung-sd-ui-manager-backend && nohup python main.py &>$LOG_PATH &
    echo "Resource Manager WebUI Started"
}

update_forge() {
    echo "Updating WebUI Forge GUI"

    cd $PROGRAM_PATH && git pull --ff-only

    cd /notebooks/ && curl https://raw.githubusercontent.com/vjumpkung/vjump-runpod-notebooks-and-script/refs/heads/main/webui-forge/launch_webui_forge.ipynb >launch_webui_forge.ipynb
    cd /notebooks/ && curl https://raw.githubusercontent.com/vjumpkung/vjump-runpod-notebooks-and-script/refs/heads/main/webui-forge/resource_manager.ipynb >resource_manager.ipynb
    cd /notebooks/ && curl https://raw.githubusercontent.com/vjumpkung/vjump-runpod-notebooks-and-script/refs/heads/main/webui-forge/ui/main.py >./ui/main.py
    cd /notebooks/ && curl https://raw.githubusercontent.com/vjumpkung/vjump-runpod-notebooks-and-script/refs/heads/main/webui-forge/ui/google_drive_download.py >./ui/google_drive_download.py

    echo "Update Completed"
}

configure_dns() {
    echo "Configuring DNS settings..."
    # Backup the current resolv.conf
    cp /etc/resolv.conf /etc/resolv.conf.backup
    # Use Google's public DNS servers
    echo "nameserver 8.8.8.8
nameserver 8.8.4.4" >/etc/resolv.conf
    echo "DNS configuration updated."
}

# Start jupyter lab
start_jupyter() {
    echo "Starting Jupyter Lab..."
    cd /notebooks/ &&
        nohup jupyter lab \
            --allow-root \
            --ip=0.0.0.0 \
            --no-browser \
            --ServerApp.trust_xheaders=True \
            --ServerApp.disable_check_xsrf=False \
            --ServerApp.allow_remote_access=True \
            --ServerApp.allow_origin='*' \
            --ServerApp.allow_credentials=True \
            --FileContentsManager.delete_to_trash=False \
            --FileContentsManager.always_delete_dir=True \
            --FileContentsManager.preferred_dir=/notebooks \
            --ContentsManager.allow_hidden=True \
            --LabServerApp.copy_absolute_path=True \
            --ServerApp.token='' \
            --ServerApp.password='' &>./jupyter.log &
    echo "Jupyter Lab started"
}

start_forge() {
    echo "Starting WebUI Forge..."
    # cd /notebooks && nohup python autolaunch_forge.py >>$PROGRAM_LOG 2>&1 &
    /bin/bash /notebooks/start_process.sh
    echo "WebUI Forge Started"
}

# Export env vars
export_env_vars() {
    echo "Exporting environment variables..."
    printenv | grep -E '^RUNPOD_|^PATH=|^_=' | awk -F = '{ print "export " $1 "=\"" $2 "\"" }' >>/etc/rp_environment
    echo 'source /etc/rp_environment' >>~/.bashrc
}

make_directory() {
    echo "create directory at $RESOURCE_PATH and output path at $OUTPUT_PATH"
    mkdir -p $RESOURCE_PATH/{checkpoints,vae,text-encoder,gfpgan,embeddings,hypernetwork,esrgan,clip,controlnet,loras}
    mkdir -p $OUTPUT_PATH
}

echo "Pod Started"
configure_dns
make_directory
export_env_vars
start_nginx
start_jupyter
update_backend
update_forge
start_backend
start_forge
echo "Start script(s) finished, pod is ready to use."
sleep infinity
