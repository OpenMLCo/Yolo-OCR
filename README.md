# Yolo-OCR
Character recognition form yolo detections


### Step by step
0. Install libraries
  ```shell
  sudo apt-get install tesseract-ocr
  pip install pytesseract
  pip install pymysql
  pip install unidecode
  sudo apt-get install poppler-utils
  pip install pdf2image
  pip install tqdm
  ```
 
1. Clone this repo
  ```shell
  git clone https://github.com/OpenMLCo/Yolo-OCR.git
  ```
2. Compile darknet
  ```shell
  cd Yolo-OCR/Yolo-OCR
  make -j2
  ```  
4. Download and include pre-training weights and database on their folder.
  ```shell
  # Descargar los pesos de la red para cedulas
  cd /content/Yolo-OCR/Yolo-OCR/Yolov4_ID/
  gdown --id 1-q3ND6ixWfsmA2JrSqk0_ZEr5sz-cl-I
  # Descargar los pesos de la red para RUT
  cd /content/Yolo-OCR/Yolo-OCR/Yolov4_RUT/
  gdown --id 1-0pu113A4EiaA4GMYP2Af2yhgFSa8p4h
  # Descargar base de datos
  cd /content/Yolo-OCR/Yolo-OCR/
  gdown --id 1A3sSqUwEVvYxmKojVRQn5eDfpZCGw3J2
  unzip files2.zip
  ```
3. Modify config.py with file paths.
7. Run demos.
  * Detect, extract, and compare between dattabases
    ```shell
    python data_validation.py
    ```    

## Credit
BIOS

## Contact us
- Daniel Garcia Murillo (danielggarciam@gmail.com)
- Julián Caicedo Acosta (julianc.caicedoa@autonoma.edu.co, juccaicedoac@gmail.com)
