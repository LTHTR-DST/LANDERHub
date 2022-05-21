# https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/1580#issuecomment-707776237
# https://zero-to-jupyterhub.readthedocs.io/en/latest/resources/reference.html#hub-extrafiles
# https://discourse.jupyter.org/t/tailoring-spawn-options-and-server-configuration-to-certain-users/8449
# https://discourse.jupyter.org/t/shared-folder-for-users-with-r-o-access-for-some-and-r-w-access-for-some-in-jupyterhub/4220/8

from kubernetes import client
from kubespawner.utils import get_k8s_model
from kubernetes.client.models import V1Volume, V1VolumeMount


TPL_RESOURCES = """
Guarantees: {cpu_guarantee} vCPU and {memory_guarantee} RAM
Limits: {cpu_limit} vCPU and {memory_limit} RAM.
"""

# ==============================================================================
# PROFILE LIST
# ==============================================================================

profiles = {
    "basic": {
        "display_name": "LANDER - Basic",
        "slug": "00_lander_basic",
        "description": """
        Basic environment for testing with Python, R and Julia. 
        """,
        "default": True,
        "kubespawner_override": {
            "mem_limit": "1G",
            "mem_guarantee": "512M",
            "cpu_limit": 0.5,
            "cpu_guarantee": 0.2,
        },
    },
    "advanced": {
        "display_name": "LANDER - Advanced",
        "slug": "20_lander_advanced",
        "description": """
        Environment for larger analytical workloads.
        """,
        "kubespawner_override": {
            "mem_limit": "6G",
            "mem_guarantee": "3G",
            "cpu_limit": 4,
            "cpu_guarantee": 1,
        },
    },
    "octave": {
        "display_name": "LANDER - Octave",
        "slug": "30_lander_octave",
        "description": """
        Provides GNU Octave kernel in addition to Python, R and Julia.
        """,
        "kubespawner_override": {
            "image": "crjupyterhub.azurecr.io/vvcb/octave-notebook:0.1.0",
            "mem_limit": "4G",
            "mem_guarantee": "2G",
            "cpu_limit": 2,
            "cpu_guarantee": 1,
        },
    },
    "fft": {
        "display_name": "LANDER - FFT Project",
        "slug": "40_lander_fft",
        "description": """
        Environment for FFT Sentiment Analysis.
        """,
        "kubespawner_override": {
            "image": "crjupyterhub.azurecr.io/vvcb/fft-notebook:0.1.0",
            "mem_limit": "2G",
            "mem_guarantee": "1G",
            "cpu_limit": 2,
            "cpu_guarantee": 1,
            "environment": {
                "fft_secret":"EUUSlbL5rp9Vn2UUak7y7sys1R-Q0Y1LGj6x6dXGPXc="
            }

        },
    },
    "rstudio": {
        "display_name": "LANDER - RStudio",
        "slug": "50_lander_rstudio",
        "description": """
        RStudio and a minimal Python 3.9 environment.
        Please see https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-r-notebook
        and https://github.com/jupyterhub/jupyter-rsession-proxy
        for installed libraries and limitations. 
        RStudio's libary management feature may not work if there are additional dependecies. 
        Use conda or mamba in a terminal to install libraries. eg. `mamba install --channel r r-tidyverse`. 
        """,
        "kubespawner_override": {
            "image": "crjupyterhub.azurecr.io/vvcb/rstudio-notebook:0.1.0",
            "mem_limit": "4G",
            "mem_guarantee": "2G",
            "cpu_limit": 2,
            "cpu_guarantee": 1,
            "default_url": "/rstudio/auth-sign-in?appUri=%2F",
        },
    },
    "gpu": {
        "display_name": "LANDER - GPU Enabled",
        "slug": "90_lander_gpu",
        "description": """
        GPU enabled cluster for accelerated ML/AI workloads.
        """,
        "kubespawner_override": {
            # "image": "crjupyterhub.azurecr.io/vvcb/tensorflow-notebook:0.1.0",
            "image": "cschranz/gpu-jupyter",
            "mem_limit": "24G",
            "mem_guarantee": "10G",
            "cpu_limit": 4,
            "cpu_guarantee": 2,
            "tolerations": [
                {
                    "key": "sku",
                    "operator": "Equal",
                    "value": "gpu",
                    "effect": "NoSchedule",
                },
            ],
            "node_selector": {"nodepool": "gpupool"},
        },
    },
    "lancuni-grp-prj-2021": {
        "display_name": "LANDER - Lancaster University Group Project 2021",
        "slug": "91_lander_lancuni-grp-prj-2021-notebook:0.1.0",
        "description": """
        Provides a bespoke Python environment with deep-learning libraries as well as R and Julia. 
        See requirements.txt for installed python libraries in shared folder.
        As this project uses small datasets, compute requirements are not expected to be high.
        Please let me know if you are hitting these limits (typically results in a dead kernel). 
        The resources allocated here are almost entirely for the Jupyter Kernel with very little consumption by other processes 
        unlike the situation where a VM maybe running a complete operating system with a graphical desktop environment.
        No GPU support (yet). 
        """,
        "kubespawner_override": {
            "image": "crjupyterhub.azurecr.io/vvcb/lancuni-grp-prj-2021-notebook:0.1.0",
            "mem_limit": "4G",
            "mem_guarantee": "3G",
            "cpu_limit": 2,
            "cpu_guarantee": 0.5,
            "node_selector": {"nodepool": "aipool"},
        },
    },
}

# ==============================================================================
# STORAGE VOLUMES AND MOUNTS
# ==============================================================================

storage_volumes = {
    "public": {
        "volume": {
            "name": "jupyterhub-shared",
            "persistentVolumeClaim": {"claimName": "pvc-aksshare-jupyterhub"},
        },
        "volume_mount": {
            "name": "jupyterhub-shared",
            "mountPath": "/home/jovyan/shared",
            "readOnly": True,
        },
    },
    "fft": {
        "volume": {
            "name": "fft-shared",
            "persistentVolumeClaim": {"claimName": "pvc-aksshare-fft"},
        },
        "volume_mount": {
            "name": "fft-shared",
            "mountPath": "/home/jovyan/shared_fft",
            "readOnly": False,
        },
    },
    "lancuni-grp-prj-2021": {
        "volume": {
            "name": "pvc-aksshare-lancuni-grp-prj-2021",
            "persistentVolumeClaim": {"claimName": "pvc-aksshare-lancuni-grp-prj-2021"},
        },
        "volume_mount": {
            "name": "pvc-aksshare-lancuni-grp-prj-2021",
            "mountPath": "/home/jovyan/shared_lancuni_grp_prj_2021",
            "readOnly": False,
        },
    },
}

# ==============================================================================
# PROFILE GROUPS
# ==============================================================================

# this applies to all users
default_profiles = [
    "basic",
    # "medium",
    "rstudio",
]

profile_groups = {
    "global": {
        # this applies to only the admin users
        "profiles": profiles.keys(),
        "users": ["vvcbx", "dobsons-max"],
    },
    "gpu": {
        "profiles": ["gpu"],
        "users": ["greyhypotheses"]
    },
    "advanced": {
        "profiles": ["advanced", "octave"],
        "users": ["vvcbx", "dobsons-max"],
    },
    "fft": {"profiles": ["fft"], "users": ["quindavies", "rohsha"]},
    "lancuni-grp-prj-2021": {
        "profiles": ["lancuni-grp-prj-2021"],
        "users": [
            "edwardau39",
            "geonzaji",
            "greyhypotheses",
            "halaawa",
            "hitu3426",
            "ignatiusezeani",
            "joshlin-ronisha",
            "mahic98",
            "messiah-rayy",
            "neethumuraleedharan",
            "prakashjp27",
            "totipotency",
            "xiongm2",
            "vvcb",
            "jobraveknight",
            "dobsons-max",
        ],
    },
}

# ==============================================================================
# STORAGE GROUPS
# ==============================================================================

default_storage = [
    "public",
]

storage_groups = {
    "global": {"volumes": storage_volumes.keys(), "users": ["vvcbx", "dobsons-max"]},
    "fft": {"volumes": ["fft"], "users": ["quindavies", "rohsha"]},
    "lancuni-grp-prj-2021": {
        "volumes": ["lancuni-grp-prj-2021"],
        "users": [
            "edwardau39",
            "geonzaji",
            "greyhypotheses",
            "halaawa",
            "hitu3426",
            "ignatiusezeani",
            "joshlin-ronisha",
            "mahic98",
            "messiah-rayy",
            "neethumuraleedharan",
            "prakashjp27",
            "totipotency",
            "xiongm2",
            "vvcb",
            "jobraveknight",
            "dobsons-max",
        ],
    },
}

# ==============================================================================

# Update profile descriptions here

for k, p in profiles.items():
    try:
        resources = TPL_RESOURCES.format(
            cpu_guarantee=p["kubespawner_override"]["cpu"]["guarantee"],
            cpu_limit=p["kubespawner_override"]["cpu"]["limit"],
            memory_guarantee=p["kubespawner_override"]["memory"]["guarantee"],
            memory_limit=p["kubespawner_override"]["memory"]["limit"],
        )
    except:
        # This should log an error regarding missing resource constraints
        resources = ""
    finally:
        p["description"] += resources
        continue


def get_profile_list(spawner):
    user = spawner.user.name

    # Todo: Is this the correct way? Should storage be linked to profiles instead?
    # Storage is linked to user rather than profile.

    profile_names = set(default_profiles)

    for g in profile_groups.values():
        if user in g["users"]:
            profile_names.update(g["profiles"])

    profile_list = []
    for i in profile_names:
        p = profiles.get(i)

        if p:
            # p["kubespawner_override"]["storage"] = {
            #     "capacity": "8Gi",
            #     "extraVolumes": volumes,
            #     "extraVolumeMounts": volume_mounts,
            # }

            profile_list.append(p)

    profile_list = sorted(profile_list, key=lambda x: x.get("slug", "99_Z"))

    return profile_list


def modify_pod_hook(spawner, pod):

    user = spawner.user.name
    volume_keys = set(default_storage)

    for s in storage_groups.values():
        if user in s["users"]:
            volume_keys.update(s["volumes"])

    for k in volume_keys:
        try:
            # get both volume and volume_mount before adding to exsiting lists.
            # Error here will skip assigning just the volume and not the mount
            volume = storage_volumes[k]["volume"]
            volume_mount = storage_volumes[k]["volume_mount"]

            pod.spec.volumes.append(get_k8s_model(V1Volume, volume))
            pod.spec.containers[0].volume_mounts.append(
                get_k8s_model(V1VolumeMount, volume_mount)
            )
        except Exception as e:
            spawner.log.error(
                f"Error mounting shared folders for {k}. Error msg: {str(e)}"
            )
            continue

    return pod


c.KubeSpawner.modify_pod_hook = modify_pod_hook
c.KubeSpawner.profile_list = get_profile_list
