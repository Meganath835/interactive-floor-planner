import numpy as np
from IPython.display import display, clear_output
import ipywidgets as widgets

print("🏠 Enhanced Floor Plan Designer with Custom Grid Size")
print("Select a room type and click on the grid to add rooms.")

# Initialize the grid with default size
grid_size = 8
grid = np.zeros((grid_size, grid_size), dtype=int)

# Room types with darker colors for better visibility
room_types = ["Empty", "Living Room", "Bedroom", "Kitchen", "Bathroom", "Dining Room", "Office", "Garage"]
room_short_names = ["E", "L", "B", "K", "T", "D", "O", "G"]
room_colors = ["white", "#4682B4", "#32CD32", "#FF8C00", "#FF69B4", "#FFFF00", "#9370DB", "#A9A9A9"]

# Text colors that contrast with the background
text_colors = ["black", "white", "black", "black", "black", "black", "black", "black"]

# Create widgets
room_selector = widgets.Dropdown(
    options=room_types[1:],
    value='Living Room',
    description='Room Type:',
    style={'description_width': 'initial'}
)

# Custom grid size input instead of fixed options
grid_size_input = widgets.IntText(
    value=8,
    min=4,
    max=100,
    description='Grid Size:',
    style={'description_width': 'initial'}
)

apply_size_btn = widgets.Button(description="Apply Grid Size", button_style='info')
clear_btn = widgets.Button(description="Clear All", button_style='danger')
status_text = widgets.Output()

# Function to update the display
def update_display():
    with status_text:
        clear_output()

        # Create a large visual representation of the grid
        html_grid = "<div style='font-family: monospace; font-size: 24px; line-height: 1.2;'>"
        html_grid += "<h3>🏠 YOUR FLOOR PLAN</h3>"
        html_grid += "<table style='border-collapse: collapse; border: 3px solid black; background-color: white;'>"

        for i in range(grid_size):
            html_grid += "<tr>"
            for j in range(grid_size):
                room_idx = grid[i, j]
                bg_color = room_colors[room_idx]
                text_color = text_colors[room_idx]
                html_grid += f"<td style='border: 2px solid black; width: 50px; height: 50px; text-align: center; vertical-align: middle; background-color: {bg_color}; color: {text_color};'><b>{room_short_names[room_idx]}</b></td>"
            html_grid += "</tr>"

        html_grid += "</table>"

        # Add legend
        html_grid += "<div style='margin-top: 20px;'><h4>Legend:</h4><table>"
        for i, room in enumerate(room_types):
            if i > 0:  # Skip Empty
                html_grid += f"<tr><td style='background-color: {room_colors[i]}; width: 30px; height: 30px; text-align: center; border: 1px solid black; color: {text_colors[i]};'><b>{room_short_names[i]}</b></td><td style='padding-left: 10px;'>{room}</td></tr>"
        html_grid += "</table></div>"

        # Count rooms
        room_counts = {room: 0 for room in room_types[1:]}
        for i in range(grid_size):
            for j in range(grid_size):
                room_idx = grid[i, j]
                if room_idx > 0:
                    room_name = room_types[room_idx]
                    room_counts[room_name] += 1

        html_grid += "<div style='margin-top: 20px;'><h4>Room Counts:</h4><ul>"
        for room, count in room_counts.items():
            if count > 0:
                html_grid += f"<li>{room}: {count} cells</li>"

        total_rooms = sum(room_counts.values())
        html_grid += f"<li><b>Total rooms: {total_rooms}</b></li>"
        html_grid += "</ul></div>"

        html_grid += "</div>"

        # Display the HTML grid
        display(widgets.HTML(value=html_grid))

# Function to handle button clicks
def on_cell_click(btn):
    i, j = btn.i, btn.j

    selected_room = room_selector.value
    room_idx = room_types.index(selected_room)

    grid[i, j] = room_idx

    # Update button appearance
    btn.description = room_short_names[room_idx]
    btn.style.button_color = room_colors[room_idx]

    # Update text color for better contrast
    if room_idx > 0:  # Not empty
        btn.style.text_color = text_colors[room_idx]
    else:
        btn.style.text_color = "black"

    # Update display
    update_display()

# Function to clear the grid
def on_clear_clicked(btn):
    global grid
    grid = np.zeros((grid_size, grid_size), dtype=int)

    # Reset all buttons
    for i in range(grid_size):
        for j in range(grid_size):
            index = i * grid_size + j
            button_grid.children[index].description = "E"
            button_grid.children[index].style.button_color = "white"
            button_grid.children[index].style.text_color = "black"

    update_display()

# Function to change grid size
def on_apply_size_clicked(btn):
    global grid_size, grid
    new_size = grid_size_input.value

    if new_size < 4:
        new_size = 4
    elif new_size > 100:
        new_size = 100

    grid_size = new_size
    grid = np.zeros((grid_size, grid_size), dtype=int)

    # Update the input field to reflect any corrections
    grid_size_input.value = grid_size

    # Recreate the button grid
    update_button_grid()
    update_display()

# Function to update button grid
def update_button_grid():
    # Clear existing buttons
    button_grid.children = []

    # Update layout
    button_grid.layout.grid_template_columns = f"repeat({grid_size}, 50px)"
    button_grid.layout.width = f'{grid_size * 55}px'

    # Create new buttons
    for i in range(grid_size):
        for j in range(grid_size):
            room_idx = grid[i, j]
            btn = widgets.Button(
                description=room_short_names[room_idx],
                layout=widgets.Layout(width='45px', height='45px'),
                style={'button_color': room_colors[room_idx], 'text_color': text_colors[room_idx]}
            )
            btn.i = i
            btn.j = j
            btn.on_click(on_cell_click)
            button_grid.children += (btn,)

# Create interactive buttons for grid cells
button_grid = widgets.GridBox(
    children=[],
    layout=widgets.Layout(
        grid_template_columns=f"repeat({grid_size}, 50px)",
        width=f'{grid_size * 55}px',
        border='2px solid black',
        padding='10px',
        background_color='white'
    )
)

# Initialize buttons
update_button_grid()

# Display the UI
display(widgets.HBox([room_selector, grid_size_input, apply_size_btn]))
display(widgets.HTML(value="<h3>Click on the grid below to add rooms:</h3>"))
display(button_grid)
display(widgets.HBox([clear_btn]))
display(status_text)

# Set up observers
apply_size_btn.on_click(on_apply_size_clicked)
clear_btn.on_click(on_clear_clicked)

# Initialize display
update_display()

# Add instructions
instructions = """
<div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-top: 20px;">
<h3>📋 Instructions:</h3>
<ol>
<li>Select a room type from the dropdown</li>
<li>Enter a custom grid size (4-20) and click "Apply Grid Size"</li>
<li>Click on a grid cell to place that room type</li>
<li>Click 'Clear All' to start over</li>
<li>The display above shows your current floor plan</li>
</ol>
<p><strong>Room Types:</strong></p>
<ul>
<li><span style="background-color: #4682B4; color: white; padding: 2px 5px;">L</span> Living Room</li>
<li><span style="background-color: #32CD32; color: black; padding: 2px 5px;">B</span> Bedroom</li>
<li><span style="background-color: #FF8C00; color: black; padding: 2px 5px;">K</span> Kitchen</li>
<li><span style="background-color: #FF69B4; color: black; padding: 2px 5px;">T</span> Bathroom</li>
<li><span style="background-color: #FFFF00; color: black; padding: 2px 5px;">D</span> Dining Room</li>
<li><span style="background-color: #9370DB; color: black; padding: 2px 5px;">O</span> Office</li>
<li><span style="background-color: #A9A9A9; color: black; padding: 2px 5px;">G</span> Garage</li>
</ul>
</div>
"""

display(widgets.HTML(value=instructions))