# https://github.com/jupyterhub/zero-to-jupyterhub-k8s/issues/1580#issuecomment-707776237
# https://zero-to-jupyterhub.readthedocs.io/en/latest/resources/reference.html#hub-extrafiles
# https://discourse.jupyter.org/t/tailoring-spawn-options-and-server-configuration-to-certain-users/8449
# https://discourse.jupyter.org/t/shared-folder-for-users-with-r-o-access-for-some-and-r-w-access-for-some-in-jupyterhub/4220/8

from datetime import datetime

from kubernetes import client
from kubernetes.client.models import (V1ObjectMeta, V1Pod, V1Volume,
                                      V1VolumeMount)
from kubespawner.spawner import KubeSpawner
from kubespawner.utils import get_k8s_model

import z2jh


def get_workspaces(spawner: KubeSpawner):
    user = spawner.user.name

    user_workspaces = set(z2jh.get_config(f"custom.users.{user}.workspaces", []))

    permitted_workspaces = []

    for user_ws in user_workspaces:

        ws = z2jh.get_config(f"custom.workspaces.{user_ws}", None)
        if ws is None:
            print(f"Workspace {user_ws} not found for user {user}")
            continue

        ws_end_date = ws.get("end_date", "1900-01-01")
        ws_end_date = datetime.strptime(ws_end_date, "%Y-%m-%d")

        ws["slug"] = user_ws

        if datetime.today() > ws_end_date:
            # expired environment
            spawner.log.info(
                f'Workspace {user_ws} expired on {ws_end_date.strftime( "%Y-%m-%d")}. Consider removing it from config.'
            )
            continue

        ws["kubespawner_override"]["extra_labels"] = {"workspace": user_ws}

        permitted_workspaces.append(ws)

    permitted_workspaces = sorted(
        permitted_workspaces, key=lambda x: x.get("slug", "99_Z")
    )

    return permitted_workspaces


def modify_pod_hook(spawner: KubeSpawner, pod: V1Pod):

    common_storage = {
        "volume": {
            "name": "landerhub-common",
            "persistentVolumeClaim": {"claimName": "pvc-landerhub-common"},
        },
        "volume_mount": {
            "name": "landerhub-common",
            "mountPath": "/home/jovyan/shared_readonly",
            "readOnly": True,
        },
    }

    try:
        # get both volume and volume_mount before adding to exsiting lists.
        # Error here will skip assigning just the volume and not the mount
        volume = common_storage["volume"]
        volume_mount = common_storage["volume_mount"]

        pod.spec.volumes.append(get_k8s_model(V1Volume, volume))
        pod.spec.containers[0].volume_mounts.append(
            get_k8s_model(V1VolumeMount, volume_mount)
        )

        spawner.log.info(f"Successfully mounted {v['name']} to {vm['mountPath']}.")

    except Exception as e:
        spawner.log.error(f"Error mounting common shared folders. Error msg: {str(e)}")

    # Add additional storage based on workspace label on pod
    # This ensures that the correct storage is mounted into the correct workspace
    try:

        metadata: V1ObjectMeta = pod.metadata

        workspace = metadata.labels.get("workspace", "")

        storage = z2jh.get_config(f"custom.workspaces.{workspace}.storage")

        spawner.log.info(f"Attempting to mount {str(storage)}...")

        if storage:
            volumes = storage["volumes"]
            volume_mounts = storage["volume_mounts"]
            for v, vm in zip(volumes, volume_mounts):
                pod.spec.volumes.append(get_k8s_model(V1Volume, v))
                pod.spec.containers[0].volume_mounts.append(
                    get_k8s_model(V1VolumeMount, vm)
                )

            spawner.log.info(f"Successfully mounted {v['name']} to {vm['mountPath']}.")
        else:
            spawner.log.info(
                f"No additional volumes to mount for '{workspace}' workspace."
            )

    except Exception as e:
        spawner.log.error(f"Error mounting workspace storage! Error msg {str(e)}")

    return pod


c.KubeSpawner.modify_pod_hook = modify_pod_hook
c.KubeSpawner.profile_list = get_workspaces
c.KubeSpawner.profile_form_template = """
        <style>
        /* The profile description should not be bold, even though it is inside the <label> tag */
        #kubespawner-profiles-list label p {
            font-weight: normal;
        }
        </style>
        <div class='form-group' id='kubespawner-profiles-list'>
        {% for profile in profile_list %}
        <label for='profile-item-{{ profile.slug }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='profile' id='profile-item-{{ profile.slug }}' value='{{ profile.slug }}' {% if profile.default %}checked{% endif %} />
            </div>
            <div class='col-md-11'>
                <strong>{{ profile.display_name }}</strong>
                {% if profile.description %}
                    <p>{{ profile.description }}
                {% endif %}
                {% if profile.kubespawner_override.image %}
                    <br><em>Image: {{ profile.kubespawner_override.image.split('/')[-1] }}</em>
                {% endif %}
                <br><em>Expires: {{ profile.end_date }}</em>
                </p>
            </div>
        </label>
        {% endfor %}
        </div>
        """
