from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-quantum-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variable to hold the Host's master key
quantum_key = ""

def generate_quantum_key():
    """Simulates QKD via Entanglement Swapping (Quantum Router)."""
    simulator = AerSimulator()
    key = ""
    
    for _ in range(256):
        # 4 Qubits: Alice(0), Host-Left(1), Host-Right(2), Bob(3)
        # 2 Classical bits to store Alice and Bob's final measurements
        qc = QuantumCircuit(4, 2)

        # --- STEP 1: INITIAL ENTANGLEMENT ---
        # Create first entangled pair (Alice & Host-Left)
        qc.h(0)
        qc.cx(0, 1)

        # Create second entangled pair (Host-Right & Bob)
        qc.h(2)
        qc.cx(2, 3)

        # --- STEP 2: ENTANGLEMENT SWAPPING (THE ROUTER) ---
        # Host performs Bell State Measurement (BSM) on its qubits (1 & 2)
        qc.cx(1, 2)
        qc.h(1)

        # --- STEP 3: CLASSICAL CORRECTION ---
        # The Host sends classical BSM results to Bob to correct his qubit.
        # If Qubit 2 is 1, apply X gate to Bob's Qubit (3)
        qc.cx(2, 3) 
        # If Qubit 1 is 1, apply Z gate to Bob's Qubit (3)
        qc.cz(1, 3)

        # --- STEP 4: KEY GENERATION ---
        # Now Alice (0) and Bob (3) are perfectly entangled! 
        # They both measure their qubits in the same basis.
        qc.measure([0, 3], [0, 1])

        # Run the simulation
        result = simulator.run(qc, shots=1).result()
        counts = result.get_counts()
        
        # The output is a 2-bit string (e.g., '00' or '11'). 
        # Because they are entangled, Alice and Bob's bits will always match.
        # We just grab one of them to build our 256-bit master key.
        measured_bit = list(counts.keys())[0][0] 
        key += measured_bit
        
    return key

def xor_cipher(text, key):
    """The Host performs the encryption routing"""
    if not key: 
        return "NO_KEY_GENERATED"
    
    encrypted_bytes = bytearray()
    for i in range(len(text)):
        char_code = ord(text[i])
        key_bit = int(key[i % len(key)])
        # XOR the character with the quantum bit
        encrypted_bytes.append(char_code ^ (key_bit * 127))
        
    return base64.b64encode(encrypted_bytes).decode('utf-8')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('request_qkd')
def handle_qkd_request():
    global quantum_key
    print("Host: Generating Master Quantum Key...")
    quantum_key = generate_quantum_key()
    
    # Notify all clients and the Host terminal
    emit('qkd_complete', {'key': quantum_key}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    global quantum_key
    sender = data['sender']
    target = data['target']
    plaintext = data['text']
    
    # 1. The Host performs the encryption
    ciphertext = xor_cipher(plaintext, quantum_key)
    
    # 2. Update the Host Terminal UI on the big screen
    emit('host_log', {
        'type': 'intercept',
        'sender': sender,
        'target': target,
        'plaintext': plaintext,
        'ciphertext': ciphertext
    }, broadcast=True)
    
    # 3. Deliver the message to the clients (Alice & Bob)
    emit('receive_message', {
        'id': data.get('id'),
        'sender': sender,
        'target': target,
        'text': plaintext,
        'encrypted': ciphertext,
        'time': data.get('time')
    }, broadcast=True)

if __name__ == '__main__':
    print("Starting Quantum Server on network (0.0.0.0:5000)...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)