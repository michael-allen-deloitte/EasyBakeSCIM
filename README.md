# EasyBakeSCIM
Master branch is working release

# Misc
## docker commands for building locally
Must be run from the same directory as the Dockerfile
```
docker build -t <human friendly image tag> .
docker run --name <container name> -p 443:443 <human friendly image tag>
```
can add -d to the docker run command if you want to run detached
## keytool command for adding cert to OPP agent:
must be run from C:\Program Files\Okta\OktaProvisioningAgent\current\jre\bin (for default installation location)
```
keytool -import -trustcacerts -keystore ..\lib\security\cacerts -storepass changeit -noprompt -alias <yourAliasName> -file <path\to\certificate.cer>
```
