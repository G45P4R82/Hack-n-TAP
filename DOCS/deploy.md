
# Deploy do Hack-n-Tap (Django + MySQL) no k3d/k3s com Ingress (Traefik)

Este guia mostra como subir o app **Django** (imagem já publicada) e um banco **MySQL** dentro do **k3s via k3d**, expor via **Ingress (Traefik)** e finalizar com:
- migrations
- staticfiles (collectstatic)
- criação de superuser

> Contexto:
- Imagem do app: `srmarinho/hack-n-tap:dev`
- App escuta na porta: `8000`
- DATABASE_URL esperado:
  - `mysql://root:tijolo44@database:3306/beerbase`
- Cluster local com k3d (k3s) + Traefik (Ingress padrão)
<img width="1090" height="889" alt="image" src="https://github.com/user-attachments/assets/16b9d18e-cdd8-4517-94d3-509e66043954" />
<img width="1090" height="889" alt="image" src="https://github.com/user-attachments/assets/16b9d18e-cdd8-4517-94d3-509e66043954" />

---

## Pré-requisitos

Tenha instalado:
- Docker
- kubectl
- k3d

Checar:
```bash
docker --version
kubectl version --client
k3d version
````

---

## 0) Criar cluster k3d expondo o Ingress

O Traefik (Ingress Controller padrão do k3s) escuta na porta 80 dentro do cluster.
Aqui mapeamos isso para `localhost:8081`.

```bash
k3d cluster create hackntap \
  -p "8081:80@loadbalancer" \
  --agents 2
```

Verificar nós:

```bash
kubectl get nodes
```

Verificar Traefik:

```bash
kubectl get pods -n kube-system | grep traefik
```

Teste rápido: (opcional, se você já testou com nginx antes, pode pular)

---

## 1) Subir MySQL no k3s (com DB já criado)

Vamos subir:

* MySQL 8
* Service com nome **database** (pra bater com o `DATABASE_URL`)
* criar automaticamente o database `beerbase`
* senha do root: `tijolo44`
* PVC pra persistir dados

Crie o arquivo: `k8s/mysql.yaml`

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hackntap

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
  namespace: hackntap
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  namespace: hackntap
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:8.0
        ports:
        - containerPort: 3306
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: tijolo44
        - name: MYSQL_DATABASE
          value: beerbase
        volumeMounts:
        - name: mysql-data
          mountPath: /var/lib/mysql
      volumes:
      - name: mysql-data
        persistentVolumeClaim:
          claimName: mysql-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: database
  namespace: hackntap
spec:
  selector:
    app: mysql
  ports:
  - port: 3306
    targetPort: 3306
```

Aplicar:

```bash
kubectl apply -f k8s/mysql.yaml
```

Checar:

```bash
kubectl -n hackntap get pods
kubectl -n hackntap logs deploy/mysql
kubectl -n hackntap get svc
```

Você deve ver o pod do mysql como `Running`.

---

## 2) Testar conexão MySQL dentro do cluster (DNS + Service)

O hostname `database` só faz sentido **dentro** do cluster.
Vamos testar usando um pod temporário `mysql-client`.

> ⚠️ Importante: se você apertar Ctrl+C no meio, pode ficar um pod “zumbi”.
> Se isso acontecer, delete ele antes de tentar de novo:
> `kubectl -n hackntap delete pod mysql-client`

Rodar client:

```bash
kubectl -n hackntap run mysql-client \
  --rm -it \
  --restart=Never \
  --image=mysql:8.0 \
  -- mysql -h database -u root -p
```

Senha:

```
tijolo44
```

Dentro do MySQL:

```sql
SHOW DATABASES;
USE beerbase;
SHOW TABLES;
```

Se `beerbase` existe, está tudo certo.

Se der erro “AlreadyExists”:

```bash
kubectl -n hackntap delete pod mysql-client
```

Se travar em ContainerCreating:

```bash
kubectl -n hackntap describe pod mysql-client
```

---

## 3) Subir o app Django (Deployment + Service + Ingress)

Crie o arquivo: `k8s/hackntap.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hackntap
  namespace: hackntap
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hackntap
  template:
    metadata:
      labels:
        app: hackntap
    spec:
      containers:
      - name: hackntap
        image: srmarinho/hack-n-tap:dev
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: mysql://root:tijolo44@database:3306/beerbase

---
apiVersion: v1
kind: Service
metadata:
  name: hackntap
  namespace: hackntap
spec:
  selector:
    app: hackntap
  ports:
  - name: http
    port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hackntap
  namespace: hackntap
  annotations:
    ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hackntap
            port:
              number: 80
```

Aplicar:

```bash
kubectl apply -f k8s/hackntap.yaml
```

Checar:

```bash
kubectl -n hackntap get pods,svc,ingress
kubectl -n hackntap logs deploy/hackntap
```

Testar pelo host:

```bash
curl -i http://localhost:8081/
```

---

## 4) Restart do Django (quando mudar env/banco/serviço)

Quando o app sobe antes do banco, ou quando muda env/Service, o pod pode precisar de restart.

Recomendado:

```bash
kubectl -n hackntap rollout restart deployment hackntap
kubectl -n hackntap rollout status deployment hackntap
```

Alternativa “machado”:

```bash
kubectl -n hackntap delete pod -l app=hackntap
```

---

## 5) Rodar migrations (obrigatório)

O log pode avisar:

* “You have unapplied migrations”
* ou rodar e dizer “No migrations to apply.”

Rodar migrations:

```bash
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py migrate
```

Ver migrations:

```bash
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py showmigrations
```

Se o migrate diz “No migrations to apply.” → ok, já está aplicado.

---

## 6) Staticfiles (collectstatic) e warning do /app/static

O warning visto foi:

* `staticfiles.W004: The directory '/app/static' in STATICFILES_DIRS does not exist.`

Isso depende de como o projeto está configurado.

### 6.1) Rodar collectstatic (quando aplicável)

Se o projeto tiver `collectstatic` configurado:

```bash
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py collectstatic --noinput
```

> Obs: Se o projeto usa settings de dev (`lhctap.settings.development`) pode não ser necessário
> ou pode estar configurado diferente. O warning não necessariamente quebra o app.

### 6.2) (Opcional) WhiteNoise (recomendado quando você controla a imagem)

Se você controla o Dockerfile/código do projeto e quer servir static “dentro do Django”:

* adicionar `whitenoise`
* configurar middleware
* definir `STATIC_ROOT`
* rodar `collectstatic`

**Isso exige rebuild da imagem.**
Como sua imagem já está publicada e pronta, só faça isso se você for manter isso no repo/app.

---

## 7) Criar superuser (admin do Django)

Criar superuser interativo:

```bash
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py createsuperuser
```

Depois acessar:

* `http://localhost:8081/admin/`

Se der erro de tabela inexistente (`no such table`), rode migrations antes:

```bash
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py migrate
```

---

## 8) Troubleshooting (o kit “por que tá dando ruim?”)

### 8.1) Logs do app

```bash
kubectl -n hackntap logs deploy/hackntap
```

### 8.2) Logs do MySQL

```bash
kubectl -n hackntap logs deploy/mysql
```

### 8.3) Ver recursos no namespace

```bash
kubectl -n hackntap get all
```

### 8.4) Eventos (muito útil)

```bash
kubectl -n hackntap get events --sort-by=.metadata.creationTimestamp
```

### 8.5) Verificar DNS/Service

```bash
kubectl -n hackntap get svc
```

O Service do MySQL precisa se chamar **database**:

* `database:3306`

### 8.6) Testar HTTP do service por dentro do cluster

```bash
kubectl -n hackntap run curl --rm -it --image=curlimages/curl -- http://hackntap
```

### 8.7) Pod “AlreadyExists” (mysql-client zumbi)

Se você cancelou com Ctrl+C:

```bash
kubectl -n hackntap delete pod mysql-client
```

---

## 9) Estrutura sugerida do repo

```
.
├── k8s/
│   ├── mysql.yaml
│   └── hackntap.yaml
└── deploy.md
```

---

## 10) Sequência rápida (TL;DR pra copiar e colar)

```bash
k3d cluster create hackntap -p "8081:80@loadbalancer" --agents 2

kubectl apply -f k8s/mysql.yaml
kubectl -n hackntap get pods
kubectl -n hackntap logs deploy/mysql

kubectl apply -f k8s/hackntap.yaml
kubectl -n hackntap get pods,svc,ingress
kubectl -n hackntap logs deploy/hackntap

kubectl -n hackntap rollout restart deploy/hackntap

kubectl -n hackntap exec -it deploy/hackntap -- python manage.py migrate
kubectl -n hackntap exec -it deploy/hackntap -- python manage.py createsuperuser

curl -i http://localhost:8081/
```
<img width="587" height="758" alt="image" src="https://github.com/user-attachments/assets/95501bc5-a62c-4e7e-85e3-bbd3f759d655" />

---

## Observações finais

* Para dev/homelab, usar MySQL root e senha hardcoded no YAML é ok.
* Para algo mais “produção”, o ideal é:

  * colocar senha e DATABASE_URL em **Secret**
  * usar usuário não-root
  * MySQL como **StatefulSet**
  * migrations via **Job** automatizado
  * readiness/liveness probes no app e no banco

```
