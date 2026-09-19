FROM python:3.11-slim

RUN apt-get update && apt-get install -y g++ make && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN g++ -std=c++17 -pthread -O2 -I include -o dpi_engine \
    src/dpi_mt.cpp src/pcap_reader.cpp src/packet_parser.cpp \
    src/sni_extractor.cpp src/types.cpp

RUN pip install --no-cache-dir fastapi uvicorn python-multipart

EXPOSE 10000
CMD ["sh", "-c", "uvicorn web.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
