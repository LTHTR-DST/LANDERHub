# Uninstall script for LANDERHub
# ====================================================================
cp -r /mnt/c/Users/vishnu.chandrabalan/.kube/config ~/.kube/config

CURRENTAKSCONTEXT=$(kubectl config current-context)
AKSNAME=aks-lander-core-prd-02
kubectl config use-context $AKSNAME
#====================================================================

NS=landerhub-prd
HELM_RELEASE_NAME=jhpvt01
Z2JH_VERSION=2.0.0

helm uninstall $HELM_RELEASE_NAME --namespace $NS
