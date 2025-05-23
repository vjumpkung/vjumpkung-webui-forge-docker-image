import dotenv
import os
import json
import subprocess
import shlex

dotenv.load_dotenv(override=True)

platform_id = "OTHER"

OUTPUT_PATH = os.getenv("OUTPUT_PATH") or "./output_images"
RESOURCE_PATH = os.getenv("RESOURCE_PATH") or "./my-runpod-volume/models"
PROGRAM_PATH = os.getenv("PROGRAM_PATH") or "./stable-diffusion-webui-forge"

if "RUNPOD_POD_ID" in os.environ.keys():
    platform_id = "RUNPOD"
elif "PAPERSPACE_FQDN" in os.environ.keys():
    platform_id = "PAPERSPACE"

FORGE_PORT = 7860

check_types = [
    "checkpoints",
    "vae",
    "text-encoder",
    "gfpgan",
    "embeddings",
    "hypernetwork",
    "esrgan",
    "clip",
    "controlnet",
    "loras",
]

argss = [
    "--ckpt-dir",
    "--vae-dir",
    "--text-encoder-dir",
    "--gfpgan-dir",
    "--embeddings-dir",
    "--hypernetwork-dir",
    "--esrgan-models-path",
    "--clip-models-path",
    "--controlnet-dir",
    "--lora-dir",
]

types_mapping = {
    "checkpoints": "ckpts",
    "vae": "vae",
    "text-encoder": "text-encoder",
    "upscale_models": "esrgan",
    "unet": "ckpts",
    "clip": "text-encoder",
    "embeddings": "embeddings",
    "controlnet": "controlnet",
    "hypernetworks": "hypernetwork",
}

patch_output_directory = {
    "outdir_txt2img_samples": "/notebooks/outputs/txt2img-images",
    "outdir_img2img_samples": "/notebooks/outputs/img2img-images",
    "outdir_extras_samples": "/notebooks/outputs/extras-images",
    "outdir_txt2img_grids": "/notebooks/outputs/txt2img-grids",
    "outdir_img2img_grids": "/notebooks/outputs/img2img-grids",
    "outdir_init_images": "/notebooks/outputs/init-images",
}


def is_posix():
    try:
        import posix

        return True
    except ImportError:
        return False


def auto_launch_forge():

    # Define subdirectories
    subdirs = [
        "txt2img-images",
        "img2img-images",
        "extras-images",
        "img2img-grids",
        "init-images",
    ]

    # Create all directories using os.path.join
    for subdir in subdirs:
        full_path = os.path.join(OUTPUT_PATH, subdir)
        os.makedirs(full_path, exist_ok=True)

    command = "python -u launch.py --loglevel WARNING --disable-console-progressbars --disable-safe-unpickle --enable-insecure-extension-access --no-download-sd-model --no-hashing --api --xformers"

    for args, value in zip(argss, check_types):
        if value == "checkpoints":
            value = "ckpts"
        model_path = os.path.join(RESOURCE_PATH, value)
        command += f" {args} {model_path}"

    proxy_url = (
        f"not found please check the provider proxy url port {FORGE_PORT} or 3001"
    )
    if platform_id == "RUNPOD":
        proxy_url = f'URL : https://{os.environ.get("RUNPOD_POD_ID")}-{FORGE_PORT}.proxy.runpod.net'
        command += f" --port {FORGE_PORT} --listen"
    elif platform_id == "PAPERSPACE":
        proxy_url = f'URL : https://tensorboard-{os.environ.get("PAPERSPACE_FQDN")}'
        command += f" --port {FORGE_PORT} --listen"
    else:
        command += f" --share --port {FORGE_PORT} --listen"

    pos = is_posix()

    print("RUNNING CMD", shlex.split(command, posix=pos))

    os.chdir(PROGRAM_PATH)  # Change to the Forge directory

    # Check if file exists; if not, create it with an empty dictionary
    config_file = "config.json"
    if not os.path.exists(config_file):
        with open(config_file, "w") as fp:
            json.dump({}, fp, indent=4)

    # Read, update, and write back the config
    with open(config_file, "r") as fp:
        load_config = json.load(fp)

    load_config.update(patch_output_directory)

    with open(config_file, "w") as fp:
        json.dump(load_config, fp, indent=4)

    # Start the subprocess with unbuffered output
    process = subprocess.Popen(
        shlex.split(command, posix=pos),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffering
    )

    print("WebUI Forge has been started")
    print(proxy_url)

    for i in process.stdout:
        print(i.strip())

    # Wait for the subprocess to complete
    process.wait()


if __name__ == "__main__":
    auto_launch_forge()
