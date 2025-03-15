#!/bin/bash
export BRANCH_ID=${BRANCH_ID:-main}
export PLATFORM_ID="RUNPOD"

start_nginx() {
    echo "Start NGINX"
    service nginx start
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

# Export env vars
export_env_vars() {
    echo "Exporting environment variables..."
    printenv | grep -E '^RUNPOD_|^PATH=|^_=' | awk -F = '{ print "export " $1 "=\"" $2 "\"" }' >>/etc/rp_environment
    echo 'source /etc/rp_environment' >>~/.bashrc
}

make_directory() {
    mkdir -p /notebooks/my-runpod-volume/models/{checkpoints,vae,text-encoder,gfpgan,embeddings,hypernetwork,esrgan,clip,controlnet,loras}
}

run_custom_script() {
    curl https://raw.githubusercontent.com/vjumpkung/vjump-runpod-notebooks-and-script/refs/heads/$BRANCH_ID/custom_script.sh -sSf | bash -s -- -y
}

echo "Pod Started"
configure_dns
start_nginx
export_env_vars
make_directory
run_custom_script
start_jupyter
echo "Start script(s) finished, pod is ready to use."
sleep infinity
