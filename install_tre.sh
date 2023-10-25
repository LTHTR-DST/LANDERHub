# Version               Date        App. version
# 1.1.3-n522.h1cc6ee89	20 May 2022	    2.3.0
# 1.1.3-n474.h8d0a7616	09 May 2022	    2.3.0
# 1.1.3-n097.hb6688f54	06 October 2021	2.0.0b1
# 1.1.3	                25 August 2021  1.4.2
# 1.2.0 Stable
# https://jupyterhub.github.io/helm-chart/

# When redeploying to same cluster with different namespace, old cluster roles cause installation to fail
# https://forum.linuxfoundation.org/discussion/858217/lab-10-1-how-to-delete-a-clusterrole-and-a-clusterrolebinding
# kubectl get clusterroles
# kubectl get clusterrolebindings
# find your role name and then delete
# kubectl delete clusterrolebinding landerhub-prd
# kubectl delete clusterrole landerhub-prd
#====================================================================
cp -r /mnt/c/Users/vishnu.chandrabalan/.kube/config ~/.kube/config

CURRENTAKSCONTEXT=$(kubectl config current-context)
AKSNAME=aks-lander-core-prd-02
kubectl config use-context $AKSNAME
#====================================================================
# need a mechanism to change this between prd and dev
NS=landerhub-prd
HELM_RELEASE_NAME=jhpvt01
Z2JH_VERSION=2.0.0

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
    --values ./helm_chart_values/users.yaml \
    --values ./helm_chart_values/workspaces.yaml \
    --set-file hub.extraFiles.customPageTemplate.stringData=./templates/custom_page.html \
    --set-file hub.extraFiles.customSpawnPageTemplate.stringData=./templates/custom_spawn.html \
    --set-file hub.extraFiles.customLogo.binaryData=./templates/lander_logo.png.b64 \
    --set-file hub.extraFiles.customOauthenticator.stringData=./hacks/oauthenticator_oauth2.py \
    --set-file hub.extraFiles.customConfig.stringData=./config/jupyterhub_config_custom.py \

#====================================================================
kubectl config use-context $CURRENTAKSCONTEXT
#====================================================================
