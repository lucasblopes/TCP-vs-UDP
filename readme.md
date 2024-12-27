# Bucket Race: TCP vs UDP Performance Comparison  

---

## Objective  
The objective of this project is to compare the performance of the **TCP** and **UDP** protocols in data transfer. This is achieved by implementing a client and a server for both protocols, measuring their performance, and analyzing the results.

---

## Description of the Bucket Race  
The Bucket Race simulates data transfer where the goal is to transfer data from a "full bucket" (a buffer with random data from RAM) on the client side to an "empty bucket" on the server side, using **TCP** and **UDP** protocols. Data is transferred in **chunks** (cup sizes), and the time taken by each protocol to transfer the entire bucket is compared.

### TCP Flow  
1. The server starts and waits for connections.  
2. The client starts, connects to the server, and sends the bucket size and cup size.  
3. The server starts timing and sends a "start" message.  
4. The client begins sending data in chunks.  
5. The server, upon receiving the final chunk, stops timing and displays the results.  

### UDP Flow with Flow Control  
1. The server starts and waits for incoming messages.  
2. The client sends the bucket size and cup size.  
3. The server starts timing and responds with a "start" message.  
4. The client sends data in chunks, and the server acknowledges each chunk with an **ACK**.  
5. The server, upon receiving the final chunk, stops timing and displays the results.  

### UDP Flow without Flow Control  
1. The server starts and waits for incoming messages.  
2. The client sends the bucket size and cup size.  
3. The server starts timing and responds with a "start" message.  
4. The client sends data in chunks without flow control (no **ACK**).  
5. The client sends an **"ENDTX"** message to indicate the end of the transfer.  
6. The server, upon receiving the "ENDTX" message, stops timing and displays the results.  

---

## Implementation Details  
- **Language**: Python 3  
- The codebase consists of:  
  - A **TCP package** containing both the client and server implementations.  
  - A **UDP package** containing both the client and server implementations.  
- The UDP client determines, via a flag in the initial message, whether to use flow control.  
- The UDP server operates with or without flow control based on the flag received from the client.  

---

## Execution  

### TCP  
1. **Run the Server**:  
   ```bash  
   python3 serverTCP.py
   ```

2. **Run the Client**:  
   ```bash  
   python3 clientTCP.py [bucket_size (kb)] [cup_size (b)]  
   ```
   
### UDP
1. **Run the Server**:  
   ```bash  
   python3 serverUDP.py
   ```

2. **Run the Client**:  
   ```bash  
   python3 clientUDP.py [bucket_size (kb)] [cup_size (b)] [useFlowControl]
   ```
