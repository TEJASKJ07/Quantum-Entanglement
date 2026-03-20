import io
import matplotlib.pyplot as plt
from PIL import Image
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_bloch_multivector

def interactive_bloch_slideshow():
    print("Pre-rendering large Bloch sphere frames. Please wait...")
    
    # --- 1. Define the 3 stages of Entanglement Swapping ---
    qc_initial = QuantumCircuit(4)
    
    qc_bell = QuantumCircuit(4)
    qc_bell.h(0)
    qc_bell.cx(0, 1)
    qc_bell.h(2)
    qc_bell.cx(2, 3)
    
    qc_swap = qc_bell.copy()
    qc_swap.cx(1, 2)
    qc_swap.h(1)
    
    steps = [
        ("1. Initial State |0000>\n(Press SPACE to advance)", qc_initial),
        ("2. Two Bell Pairs (0&1, 2&3)\n(Arrows shrink to 0)", qc_bell),
        ("3. Swapped! (0&3 entangled)\n(Arrows remain at 0)", qc_swap)
    ]
    
    frames = []
    
    # --- 2. Pre-render everything invisibly ---
    plt.ioff() 
    
    for title, qc in steps:
        state = Statevector(qc)
        
        # INCREASED SIZE: Made the figure much wider and taller for 4 spheres
        fig = plot_bloch_multivector(state, title=title, figsize=(16, 5))
        
        buf = io.BytesIO()
        # INCREASED DPI: Makes the image sharper when rendered large
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        
        img = Image.open(buf)
        frames.append(img.copy()) 
        
        plt.close(fig) 
        buf.close()

    print("Rendering complete! Opening interactive viewer...")

    # --- 3. Create the Large Interactive Window ---
    # Make the display window match our large frames
    fig_slides, ax_slides = plt.subplots(figsize=(16, 6))
    ax_slides.axis('off') 
    
    # Load the first frame
    im_display = ax_slides.imshow(frames[0])
    
    # --- 4. The Keyboard Event Engine ---
    # We use a list to store the current frame index so we can update it inside the function
    current_frame = [0] 

    def on_press(event):
        # Check if the spacebar was pressed
        if event.key == ' ':
            # Move to the next frame, and loop back to 0 if we hit the end
            current_frame[0] = (current_frame[0] + 1) % len(frames)
            im_display.set_data(frames[current_frame[0]])
            fig_slides.canvas.draw()

    # Connect the keyboard press event to our function
    fig_slides.canvas.mpl_connect('key_press_event', on_press)
    
    # Set the window title so it's clear
    fig_slides.canvas.manager.set_window_title('Quantum Entanglement Swapping (Press Space)')
    
    plt.show()

if __name__ == "__main__":
    interactive_bloch_slideshow()