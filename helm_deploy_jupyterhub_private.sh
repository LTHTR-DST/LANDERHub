# Version               Date	        App. version
# 1.1.3-n474.h8d0a7616	09 May 2022	2.3.0
# 1.1.3-n097.hb6688f54	06 October 2021	2.0.0b1
# 1.1.3	                25 August 2021	1.4.2
# 1.2.0 Stable
# https://jupyterhub.github.io/helm-chart/


# need a mechanism to change this between prd and dev
NS=jupyterhub-prd 
HELM_RELEASE_NAME=jhpvt01
Z2JH_VERSION=1.2.0

helm upgrade \
    --cleanup-on-fail \
    --install $HELM_RELEASE_NAME jupyterhub/jupyterhub \
    --namespace $NS \
    --create-namespace \
    --version $Z2JH_VERSION \
    --values ./helm_chart_values/cull.yaml \
    --values ./helm_chart_values/hub.yaml \
    --values ./helm_chart_values/ingress.yaml \
    --values ./helm_chart_values/proxy.yaml \
    --values ./helm_chart_values/singleuser.yaml \
    --set-file hub.extraFiles.customConfig.stringData=./config/jupyterhub_config_custom.py \
    --set-file hub.extraFiles.customPage.stringData=./templates/custom_page.html \
    --set-file hub.extraFiles.customLogo.binaryData=./templates/lander_logo.png.b64