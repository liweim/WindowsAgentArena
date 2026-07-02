# Server side
## Add your tasks to this folder, following the same structure used in OSWorld

```text
/home/weimingli/projects/WindowsAgentArena/src/win-arena-container/client/evaluation_examples_windows/examples/accessibility/
```

## Run a task to verify it manually

```bash
conda activate winarena
cd /home/weimingli/projects/WindowsAgentArena/scripts
python run_human.py --example ../src/win-arena-container/client/evaluation_examples_windows/examples/accessibility/hearing/Access-chrome_live_caption.json
```

# Client side
## Connect remotely using Windows App

### Config ssh in your vscode-config
```text
Host CSE_LOGIN
  HostName login.cse.unsw.edu.au
  User your-zID
  ForwardX11 Yes

Host CSE_T2
  HostName 129.94.175.253
  User your-name
  ProxyJump CSE_LOGIN
  LocalForward 3390 127.0.0.1:3390
```

### Open the SSH tunnel

```bash
ssh -N -L 3390:localhost:3390 CSE_T2
```

### Open **Windows App** and enter the following address to connect

```text
localhost:3390
```

### Login credentials

```text
Username: .\Docker
Password: (leave blank)
```

# Self-hosted services

## Access locally
Add `LocalForward <port> 127.0.0.1:<port>` under your CSE_T2 SSH config, then connecting with ssh CSE_T2 and opening http://localhost:<port>/ in your browser while keeping the SSH session open.

## Shopping Website (OneStopShop)
```bash
cd ~/docker-images
docker load --input shopping_final_0712.tar
docker run --name shopping -p 7770:80 -d shopping_final_0712
# wait ~1 min to wait all services to start

docker exec shopping /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7770"
docker exec shopping mysql -u magentouser -pMyPassword magentodb -e  'UPDATE core_config_data SET value="http://localhost:7770/" WHERE path = "web/secure/base_url";'
docker exec shopping /var/www/magento2/bin/magento cache:flush
```
Now you can visit http://localhost:7770.

## E-commerce Content Management System (CMS)
```bash
docker load --input shopping_admin_final_0719.tar
docker run --name shopping_admin -p 7780:80 -d shopping_admin_final_0719
# wait ~1 min to wait all services to start

docker exec shopping_admin /var/www/magento2/bin/magento setup:store-config:set --base-url="http://localhost:7780"
docker exec shopping_admin mysql -u magentouser -pMyPassword magentodb -e  'UPDATE core_config_data SET value="http://localhost:7780/" WHERE path = "web/secure/base_url";'
docker exec shopping_admin /var/www/magento2/bin/magento cache:flush
```
Now you can access to http://localhost:7780/admin. Account for shopping_admin：
```text
username: admin
password: admin1234
```

## Wikipedia
```bash
docker run -d --name=wikipedia --volume=./:/data -p 8888:80 ghcr.io/kiwix/kiwix-serve:3.3.0 wikipedia_en_all_maxi_2022-05.zim
```
Now you can visit http://localhost:8888/wikipedia_en_all_maxi_2022-05/A/User:The_other_Kiwix_guy/Landing.

## Reddit
```bash
docker load --input postmill-populated-exposed-withimg.tar
docker run --name forum -p 9999:80 -d postmill-populated-exposed-withimg
```
Now you can visit http://localhost:9999/.

## CAPTCHA
```bash
cd scripts
bash run_captcha_service.sh
```