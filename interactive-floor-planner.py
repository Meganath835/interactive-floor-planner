import numpy as np
from IPython.display import display, clear_output
import ipywidgets as widgets
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.model_selection import train_test_split

# --- MongoDB Connection ---
# Paste your MongoDB Atlas connection string here
# client = MongoClient('mongodb+srv://<username>:<password>@yourcluster.mongodb.net/?retryWrites=true&w=majority')
# For local testing:
client = MongoClient('mongodb+srv://Username:Password@ClusterName.mongodb.net/?retryWrites=true&w=majority&appName=ClusterName')

db = client['architectural_floor_plans']
collection = db['plans']

print("🏠 AI-Powered Floor Plan Designer with Custom Naming & Enhanced Suggestions")

# Initialize grid and room properties
grid_size = 8
grid = np.zeros((grid_size, grid_size), dtype=int)
room_types = ["Empty", "Living Room", "Bedroom", "Kitchen", "Bathroom", "Dining Room", "Office", "Garage"]
room_short_names = ["E", "L", "B", "K", "T", "D", "O", "G"]
room_colors = ["white", "#4682B4", "#32CD32", "#FF8C00", "#FF69B4", "#FFFF00", "#9370DB", "#A9A9A9"]
text_colors = ["black", "white", "black", "black", "black", "black", "black", "black"]
selected_cell = None

# --- TinyML Model Simulation (No changes here) ---
def generate_training_data(num_samples=5000):
    X, y, num_room_types = [], [], len(room_types)
    for _ in range(num_samples):
        neighbors = np.random.randint(0, num_room_types, size=4)
        target_room = 0
        if room_types.index("Bedroom") in neighbors and np.random.rand() > 0.3: target_room = room_types.index("Bathroom")
        elif room_types.index("Kitchen") in neighbors and np.random.rand() > 0.4: target_room = room_types.index("Dining Room")
        elif room_types.index("Living Room") in neighbors and np.random.rand() > 0.7: target_room = room_types.index("Dining Room")
        else: target_room = np.random.choice([room_types.index("Bedroom"), room_types.index("Office"), room_types.index("Living Room")])
        X.append(neighbors)
        y.append(target_room)
    X_one_hot = tf.keras.utils.to_categorical(X, num_classes=num_room_types).reshape(-1, 4 * num_room_types)
    y_one_hot = tf.keras.utils.to_categorical(y, num_classes=num_room_types)
    return X_one_hot, y_one_hot

def create_tinyml_model():
    model = Sequential([
        Dense(16, activation='relu', input_shape=(4 * len(room_types),)),
        Dense(16, activation='relu'),
        Dense(len(room_types), activation='softmax')])
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    return model

X_data, y_data = generate_training_data()
tinyml_model = create_tinyml_model()
tinyml_model.fit(X_data, y_data, epochs=20, batch_size=32, verbose=0)
print("✅ TinyML model trained and ready.")


# --- Widgets ---
room_selector = widgets.Dropdown(options=room_types[1:], value='Living Room', description='Room Type:')
grid_size_input = widgets.IntText(value=8, min=4, max=100, description='Grid Size:')
apply_size_btn = widgets.Button(description="Apply Size", button_style='info')
clear_btn = widgets.Button(description="Clear All", button_style='danger')
plan_name_input = widgets.Text(value='', placeholder='Name your floor plan', description='Plan Name:') # NEW WIDGET
save_btn = widgets.Button(description="Save to DB", button_style='success')
load_btn = widgets.Button(description="Load from DB", button_style='primary')
ai_suggest_btn = widgets.Button(description="💡 AI Suggest", button_style='warning', tooltip="Click an empty cell, then this button")
plan_selector = widgets.Dropdown(description='Saved Plans:')
suggestion_box = widgets.HBox([]) # NEW WIDGET for AI suggestion buttons
status_text = widgets.Output()


# --- Core Functions ---

def update_plan_selector():
    plans = list(collection.find({}, {"name": 1, "timestamp": 1}))
    plan_options = [("Select a plan", None)] + [(p.get('name', 'Unnamed'), p['_id']) for p in plans]
    plan_selector.options = plan_options

def on_save_clicked(b):
    """Saves the plan with a custom name or a timestamp fallback."""
    plan_name = plan_name_input.value.strip() # Get name from the new text box
    if not plan_name: # If the user left it blank
        plan_name = "FloorPlan_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    plan_data = {"name": plan_name, "grid_size": grid_size, "grid": grid.tolist(), "timestamp": datetime.datetime.now()}
    collection.insert_one(plan_data)
    update_plan_selector()
    with status_text:
        clear_output()
        print(f"✅ Plan '{plan_name}' saved successfully!")
    plan_name_input.value = '' # Clear the input box after saving
    update_display()

def on_ai_suggest_clicked(b):
    """NEW: Generates and displays the top 3 room suggestions as buttons."""
    global grid
    suggestion_box.children = [] # Clear previous suggestions
    if selected_cell:
        i, j = selected_cell
        if grid[i, j] == 0:
            neighbors = []
            for di, dj in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                ni, nj = i + di, j + dj
                neighbors.append(grid[ni, nj] if 0 <= ni < grid_size and 0 <= nj < grid_size else 0)
            
            input_data = tf.keras.utils.to_categorical([neighbors], num_classes=len(room_types)).reshape(1, -1)
            prediction = tinyml_model.predict(input_data, verbose=0)
            
            # Get top 3 suggestions, excluding "Empty"
            sorted_indices = np.argsort(prediction[0])[::-1]
            top_suggestions = []
            for idx in sorted_indices:
                if idx != 0: # Exclude "Empty"
                    top_suggestions.append(idx)
                if len(top_suggestions) == 3:
                    break

            # Create a button for each suggestion
            suggestion_buttons = []
            for room_idx in top_suggestions:
                btn = widgets.Button(description=room_types[room_idx], button_style='info')
                
                def on_suggestion_chosen(b):
                    chosen_room_name = b.description
                    chosen_room_idx = room_types.index(chosen_room_name)
                    grid[i, j] = chosen_room_idx
                    suggestion_box.children = [] # Hide buttons after choice
                    update_button_grid()
                    update_display()
                
                btn.on_click(on_suggestion_chosen)
                suggestion_buttons.append(btn)
            
            suggestion_box.children = suggestion_buttons # Display the new buttons

def on_cell_click(btn):
    """Optimized cell click handler."""
    global grid, selected_cell
    i, j = btn.i, btn.j
    selected_cell = (i, j)
    suggestion_box.children = [] # Clear AI suggestions when user clicks elsewhere
    
    selected_room_idx = room_types.index(room_selector.value)
    new_room_idx = selected_room_idx if grid[i, j] != selected_room_idx else 0
    grid[i, j] = new_room_idx

    # Direct button update for speed
    btn.description = room_short_names[new_room_idx]
    btn.style.button_color = room_colors[new_room_idx]
    btn.style.text_color = text_colors[new_room_idx]
    
    update_display()

# --- Other UI and Helper Functions (Largely Unchanged) ---

def on_load_clicked(b):
    global grid_size, grid
    plan_id = plan_selector.value
    if plan_id:
        plan_data = collection.find_one({"_id": ObjectId(plan_id)})
        if plan_data:
            grid_size = plan_data['grid_size']
            grid = np.array(plan_data['grid'])
            grid_size_input.value = grid_size
            update_button_grid()
            update_display()
            with status_text:
                clear_output()
                print(f"✅ Plan '{plan_data.get('name', 'Unnamed')}' loaded.")

def update_display():
    with status_text:
        clear_output()
        html_grid = "<h3>🏠 YOUR FLOOR PLAN</h3><table style='border-collapse: collapse; border: 3px solid black;'>"
        for i in range(grid_size):
            html_grid += "<tr>"
            for j in range(grid_size):
                room_idx = grid[i, j]
                border_style = "3px solid #0000FF" if selected_cell == (i, j) else "2px solid black"
                html_grid += f"<td style='border: {border_style}; width: 40px; height: 40px; text-align: center; background-color: {room_colors[room_idx]}; color: {text_colors[room_idx]};'><b>{room_short_names[room_idx]}</b></td>"
            html_grid += "</tr>"
        html_grid += "</table>"
        # (You can add legend/room counts back here if desired)
        display(widgets.HTML(value=html_grid))

def on_clear_clicked(b):
    global grid
    grid = np.zeros((grid_size, grid_size), dtype=int)
    update_button_grid()
    update_display()
    
def on_apply_size_clicked(b):
    global grid_size, grid
    grid_size = grid_size_input.value
    grid = np.zeros((grid_size, grid_size), dtype=int)
    update_button_grid()
    update_display()

def update_button_grid():
    buttons = []
    for i in range(grid_size):
        for j in range(grid_size):
            btn = widgets.Button(
                description=room_short_names[grid[i, j]],
                layout=widgets.Layout(width='40px', height='40px'),
                style={'button_color': room_colors[grid[i, j]], 'text_color': text_colors[grid[i, j]]}
            )
            btn.i, btn.j = i, j
            btn.on_click(on_cell_click)
            buttons.append(btn)
    button_grid.children = buttons
    button_grid.layout.grid_template_columns = f"repeat({grid_size}, 45px)"
    button_grid.layout.width = f'{grid_size * 50}px'

# --- UI Layout ---
button_grid = widgets.GridBox(children=[], layout=widgets.Layout())
update_button_grid()
update_plan_selector()

# Display UI Components in order
display(widgets.HBox([room_selector, grid_size_input, apply_size_btn]))
display(widgets.HTML(value="<h3>Click on the grid to add/remove rooms:</h3>"))
display(button_grid)
display(widgets.HBox([clear_btn, plan_selector, load_btn, ai_suggest_btn]))
display(widgets.HBox([plan_name_input, save_btn])) # NEW layout for saving
display(suggestion_box) # Box for AI suggestion buttons
display(status_text)

# Observers
apply_size_btn.on_click(on_apply_size_clicked)
clear_btn.on_click(on_clear_clicked)
save_btn.on_click(on_save_clicked)
load_btn.on_click(on_load_clicked)
ai_suggest_btn.on_click(on_ai_suggest_clicked)

update_display()


display(widgets.HTML(value=instructions))

