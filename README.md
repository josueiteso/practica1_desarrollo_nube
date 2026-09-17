# Requisitos

- Tener configurada una instancia de Ubuntu mediante WSL (o usar Linux/MacOS)
- En la instancia de ubuntu:
  - Tener configurado AWS CLI con tus credenciales de AWS.
  - Tener instalado CURL
  - Tener instalado PSQL

# Como montar la aplicacion

## Paso 1: Clonar el repositorio

```bash
git clone https://github.com/josueiteso/practica1_desarrollo_nube.git
```

## Paso 2: Crear la instancia de RDS

1. Ve a Aurora and RDS -> Create database -> Full Configuration
3. Engine type: PostgreSQL. Ojo, no confundir con Aurora (PostgreSQL Compatible)
4. Templates: Free tier
5. DB instance identifier: instabox-rds (o el nobre que quieras)
6. DB master username: instabox_user (o el nombre que quieras)
7. Credentials management: Managed in AWS Secrets Manager
8. En Connectivity deja el VPC default y en "VPC security group (firewall)" elige "Create new" y ponle de nombre instabox-rds-sg (o lo que quieras)
9. Aun en Connectivity, Public access: Yes

Todo lo demas pude quedarse en el default. Has click en "Create database" y espera a que su estatus diga "Available". Puede tardar unos minutos.

### Crear las tablas events y photos

Primero tenemos que editar las inbound rules del security group que creamos para poder conectarnos a la instancia. Ve a EC2 -> Security Groups -> instabox-rds-sg (o lo que lo hallas llamado) -> Edit inbound rules y agrega:

Type = PostgreSQL, Source = Anywhere-IPv4 (0.0.0.0/0)

Ahora abre una terminal y conectate a tu instancia de Ubuntu mediante WSL. Una ves conectado recomiendo hacer esto desde el directorio home. Puedes navegar a el con el comando "cd ~".

En tu instancia de RDS ya deberian aparecer los Connection steps en "Connectivity & security". En "Programming language" elige "PSQL (Linux)" y copia y pega los comandos que se muestran ahi. Por ejemplo en mi caso son estos:

```bash
curl -o global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

export RDSHOST="instabox-db.ckbnunkcbkk7.us-east-1.rds.amazonaws.com"
psql "host=$RDSHOST port=5432 dbname=postgres user=instabox_user sslmode=verify-full sslrootcert=./global-bundle.pem password=$(aws secretsmanager get-secret-value --secret-id 'arn:aws:secretsmanager:us-east-1:421634813733:secret:rds!db-c7b1413c-970d-4b3d-8d1c-fd8cb84c85c0-RWZBBx' --query SecretString --output text | jq -r '.password')"
```

Si no funciona, checa que ejecutaste el segundo comando en el mismo directorio donde ejecutaste el primero. Puedes checar con "ls -lah" si el archivo global-bundle.pem esta presente en tu directorio actual.

Una ves conectado a tu instancia RDS con PSQL, crea ambas tablas. Puedes revisar si se crearon con el comando "\dt":

```sql
CREATE TABLE events (
    event_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name VARCHAR(255) NOT NULL,
    event_type  VARCHAR(100) NOT NULL,
    event_date  DATE NOT NULL
);

CREATE TABLE photos (
    photo_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id      UUID NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    original_key  VARCHAR(255) NOT NULL,
    polaroid_key  VARCHAR(255) NOT NULL,
    message       TEXT
);
```

## Paso 3: Crear buckets de S3

Vea S3 -> Create Bucket

1. Bucket name: `<tu nombre para el bucket de pictures aqui>` (el nombre de los buckets es unico globalmente asi que elige algo por tu cuenta)
2. Deja lo demas por default
3. Has click en Create bucket
4. Has lo mismo para el bucket de polaroids

## Paso 4: Crea la instancia de EC2

Ve a EC2 -> Launch instances

1. Name: instabox-ec2 (o lo que quieras)
2. AMI (Amazon Machine Image): Ubuntu. Puedes dejar la default.
3. Key pair (login): Crea una nueva (ej: instabox-keypair) y descarga el .pem. Toma nota de la ruta del archivo, la necesitaras para conectarte a la insatancia EC2
4. Network settings -> Edit: Crea un nuevo security group llamado instabox-ec2-sg (o lo que quieras) y agrega una regla de entrada Custom TCP (8000) desde Anywhere (0.0.0.0/0). Deja todo lo demas en su default.
5. Advanced details -> IAM instance profile: LabInstanceProfile
6. Launch instance

Tardara unos minutos en inicializarse

## Paso 5: Conectar a la instancia de EC2 y copiar el repositorio

Para correr los siguientes comandos tienes que tener a la mano la ruta donde esta el archivo .pem que creaste, la ruta del repositorio clonado y la direccion DNS publica de tu instancia EC2.

Primero que nada, copia tu archivo .pem a tu instancia de Ubuntu. Este comando especifico lo copia al directorio home (~):

```bash
cp ruta/a/tu/instabox-keypair.pem ~/instabox-keypair.pem
```

Esto lo hacemos porque a continuacion vamos a ejecutar chmod 400 para asegurarle al ssh que la llave no es visible publicamente. Y por alguna razon el comando no funciona si el archivo .pem se encuentra en un directorio de windows:

```bash
chmod 400 ruta/a/tu/instabox-keypair.pem
```

Y conectate mediante ssh:

```bash
ssh -i ruta/a/tu/instabox-keypair.pem ubuntu@<la dns publica de tu instancia ec2>
```

Ahora, desde WSL (otra terminal, no la del ssh) copia el repositorio a tu instancia de ec2 mediante el comando scp:

```bash
scp -i ruta/a/tu/instabox-keypair.pem -r /ruta/a/tu/practica1_desarrollo_nube ubuntu@<la dns publica de tu instancia ec2>:~/practica1_desarrollo_nube
```

## Paso 6: Ejecuta la aplicacion

De vuelta en la terminal ssh:

1. Navega al directorio del repositorio e instala las dependencias:

Primero instala python en la instancia:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

Y luego navegas al directorio del proyecto, activas el venv e instalas las dependencias:

```bash
cd ~/practica1_desarrollo_nube
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configura las variables de entorno

Necesitamos:

- `AWS_REGION`: siempre la misma donde creaste todo esto, en mi caso us-east-1.
- `DB_SECRET_ARN`: el string que aparece en el "Masters credentials ARN" de tu instancia RDS. De aqui es que la aplicacion leera las credenciales de la base de datos
- `DB_ENDPOINT`: el endpoint que aparece cuando vas a Connectivity & security -> Endpoints -> Additional Configurations en tu instancia RDS
- `DB_NAME`: postgres
- `PICTURES_BUCKET`: el nombre que le pusiste a tu bucket de pictures
- `POLAROIDS_BUCKET`: el nombre que le pusiste a tu bucket de polaroids.

Cuando encuentres esos valores, llenalos en los siguientes comandos y ejecutalos en el directorio del repositorio:

```bash
export AWS_REGION=
export DB_SECRET_ARN=
export DB_ENDPOINT=
export DB_NAME=
export PICTURES_BUCKET=
export POLAROIDS_BUCKET=
```

Por ejemplo, en mi caso fue:

```bash
export AWS_REGION=us-east-1
export DB_SECRET_ARN='arn:aws:secretsmanager:us-east-1:421634813733:secret:rds!db-6517a77a-9a4f-44de-ab06-7c29e676a1d7-TJfObg'
export DB_ENDPOINT='instabox-rds.ckbnunkcbkk7.us-east-1.rds.amazonaws.com'
export DB_NAME='postgres'
export PICTURES_BUCKET='instabox-bucket-pictures'
export POLAROIDS_BUCKET='instabox-bucket-polaroids'
```

3. Corre el programa:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Y listo. La aplicacion se inicializara en un puerto TCP 8000. Ahora puedes enviar solicitudes con Postman o CURL con la dirrecion ip publica de la instancia ec2 y el puerto:

```
http://<direccion ipv4 publica de ec2>:8000
```

## Paso 7: Elimina los recursos

Si no vas a usar mas la aplicacion asegurate de borrar los recursos para que no incurras costos por servicios que no usas. Los recursos relevantes son:

**La instancia RDS**: seleccionala, has click en "Actions" -> "Delete" y confirma que lo quieres borrar.

**La instancia EC2**: has click derecho en la instancia -> Terminate (delete) instance y confirma. Puede tardar un tiempo en desaparecer del dashboard.

**Buckets S3**: elimina todos los archivos de los buckets, seleccionalos y has click en "Delete". Confirma.

**Secrets**: si seguiste la guia al pie de la letra entonces el secret se habra eliminado junto con la instancia RDS ya que se creo junto a la instancia. Pero por si acaso checa los secrets que tienes en Secrets Manager y borralo si lo encuentras.

**Security groups**: Ve a VPC y EC2 a security groups y borra los security groups que creaste con click derecho -> Delete security groups.
