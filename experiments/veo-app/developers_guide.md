# Developer's Guide

Welcome to the GenMedia Creative Studio application! This guide provides an overview of the application's architecture and a step-by-step tutorial for adding new pages. Its purpose is to help you understand the project's structure and contribute effectively.

## Application Architecture

This application is built using Python with the [Mesop](https://mesop-dev.github.io/mesop/) UI framework and a [FastAPI](https://fastapi.tiangolo.com/) backend. The project is structured to enforce a clear separation of concerns, making the codebase easier to navigate, maintain, and extend.

Here is a breakdown of the key directories and their roles:

*   **`main.py`**: This is the main entry point of the application. It is responsible for:
    *   Initializing the FastAPI server.
    *   Mounting the Mesop application as a WSGI middleware.
    *   Handling root-level routing for authentication and redirects.
    *   Applying global middleware, such as the Content Security Policy (CSP).

*   **`pages/`**: This directory contains the top-level UI code for each distinct page in the application (e.g., `/home`, `/imagen`, `/veo`). Each file in this directory typically defines a function that builds the UI for a specific page using Mesop components.

*   **`components/`**: This directory holds reusable UI components that are used across multiple pages. For example, the page header, side navigation, and custom dialogs are defined here. This promotes code reuse and a consistent look and feel.

*   **`models/`**: This is where the core business logic of the application resides. It contains the code for interacting with backend services, such as:
    *   Calling Generative AI models (e.g., Imagen, Veo).
    *   Interacting with databases (e.g., Firestore).
    *   Handling data transformations and other business logic.

*   **`state/`**: This directory defines the application's state management classes using Mesop's `@me.stateclass`. These classes hold the data that needs to be shared and preserved across different components and user interactions.

*   **`config/`**: This directory is for application configuration. It includes:
    *   `default.py`: For defining default application settings and loading environment variables.
    *   `navigation.json`: For configuring the application's side navigation.
    *   `rewriters.py`: For storing the prompt templates used by the AI models.

## Core Development Patterns and Lessons Learned

This section outlines the key architectural patterns and best practices that are essential for extending this application. Adhering to these conventions will help you avoid common errors and build features that are consistent with the existing codebase.

### Mesop UI and State Management

1.  **Co-locating Page State:**
    *   **Problem:** A page fails to load and throws a `NameError: name 'PageState' is not defined`.
    *   **Solution:** For state that is specific to a single page, the `@me.stateclass` definition **must** be in the same file as the `@me.page` function and its associated event handlers. This ensures that the state class is always in the correct scope. Only the global `AppState` should be in its own file (`state/state.py`).

2.  **Correctly Handling Event Handlers:**
    *   **Problem:** A UI element, like a slider or button, does not update the UI when interacted with.
    *   **Solution:** The function directly assigned to an event handler (e.g., `on_value_change`, `on_click`) must be the generator function that `yield`s. Using a `lambda` to call another generator function will break the UI update chain, and the component will not refresh.

3.  **Building Custom Components from Primitives:**
    *   **Problem:** The application crashes with an `AttributeError`, indicating that a Mesop component or type (e.g., `me.icon_button`, `me.EventHandler`) does not exist.
    *   **Solution:** Do not assume a component or type exists. When an `AttributeError` occurs, build the desired functionality from more primitive, guaranteed components. For example, a clickable icon can be reliably constructed using a `me.box` with an `on_click` handler that contains a `me.icon`.

4.  **Introspecting Custom Components:**
    *   **Problem:** The application crashes with a `TypeError` about an unexpected keyword argument when using a component from the `components/` directory (e.g., `components/dialog.py`).
    *   **Solution:** This project contains custom components. Unlike standard Mesop components, their specific API (the parameters they accept) is defined within this project. If you encounter a `TypeError` when using a custom component, do not guess its parameters. **Read the component's source file** to understand its exact function signature and use it accordingly.

5.  **Passing Data from Loops to Event Handlers:**
    *   **Problem:** An event handler for an item in a list always receives data from the *last* item in the list, regardless of which item was clicked.
    *   **Solution:** When creating a list of clickable components inside a `for` loop, you often need to know which specific item was clicked. The standard Mesop pattern for this is to pass the unique identifier of the item (e.g., its ID or a GCS URI) to the `key` property of the clickable component (like `me.box`). The event handler function will then receive this identifier in the `e.key` attribute of the event object.

### Data and Metadata Handling

1.  **Favor Flexible Generalization Over Brittle Replacement:**
    *   **Problem:** When refactoring, a specialized function (e.g., `add_vto_metadata`) is replaced by a generic one, but this new function loses the ability to handle the specific data fields of the original.
    *   **Solution:** When refactoring, favor generalization and flexibility. Instead of removing a specialized function, adapt the new, more general function to handle the specialized cases by accepting more flexible arguments (like `**kwargs`). This ensures no data is lost and the system can be extended more easily in the future.

2.  **Ensure Unique Filenames:**
    *   **Problem:** Generated files in Google Cloud Storage are being overwritten.
    *   **Solution:** When saving dynamically generated content (like images, videos, or audio files), always generate a unique filename for each asset. A good practice is to use Python's `uuid` module (e.g., `f"my_file_{uuid.uuid4()}.png"`) to create a universally unique identifier for each file.

### Backend and Frontend Consistency

*   **Problem:** A generated image appears stretched or improperly fitted in its UI container.
*   **Solution:** Ensure that parameters used in backend API calls (e.g., `models.image_models.generate_image_for_vto`) match the expectations of the frontend UI components that will display the result. For example, if a UI container is styled to be square (`1:1`), the corresponding API call to generate an image for that container should request a `1:1` aspect ratio. Mismatches will lead to distorted or improperly fitted media.

## Firestore Setup

This application uses Firestore to store metadata for the media library and user sessions. Here's how to set it up:

1.  **Create a Firestore Database:** In your Google Cloud Project, create a Firestore database in Native Mode.

2.  **Create Collections:**
    *   Create a collection named `genmedia` (or as configured by `GENMEDIA_COLLECTION_NAME`).
    *   Create a collection named `sessions` (or as configured by `SESSIONS_COLLECTION_NAME`).

3.  **Create an Index:** For the `genmedia` collection, create a single-field index for the `timestamp` field with the query scope set to "Collection" and the order set to "Descending". This will allow the library to sort media by the time it was created. The `sessions` collection does not require a custom index for its default functionality.

4.  **Set Security Rules:** To protect your data, set the following security rules in the "Rules" tab of your Firestore database. These rules ensure that users can only access their own media and session data.

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Match any document in the 'genmedia' collection
    match /genmedia/{docId} {
      // Allow read and write access only if the user is authenticated
      // and their email matches the 'user_email' field in the document.
      allow read, write: if request.auth != null && request.auth.token.email == resource.data.user_email;
    }

    // Match any document in the 'sessions' collection
    match /sessions/{sessionId} {
      // Allow read and write access only if the user is authenticated
      // and their email matches the 'user_email' field in the document.
      allow read, write: if request.auth != null && request.auth.token.email == resource.data.user_email;
    }
  }
}
```

## Authentication and Session Management

A critical architectural challenge in this application is bridging the context gap between the FastAPI backend and the Mesop UI framework. A direct middleware approach to authentication fails because the middleware runs outside the Mesop application context, leading to runtime errors.

To solve this, we use a **redirect-based authentication pattern**. This ensures that user and session information is correctly established before any Mesop page is rendered.

Here is the flow:

1.  **Root Redirect:** The FastAPI route for `/` redirects all initial traffic to a dedicated authentication endpoint, `/__/auth/`.

2.  **Authentication Endpoint (`/__/auth/`):** This FastAPI endpoint is responsible for:
    *   Reading the user's identity from the `X-Goog-Authenticated-User-Email` header.
    *   Retrieving a unique `session_id` from the request's cookies. If no cookie is present, a new `session_id` is generated.
    *   Persisting the session data (user email and session ID) to the `sessions` collection in Firestore.
    *   Storing the `user_email` and `session_id` on the global `app.state` object. This object serves as the critical bridge between the FastAPI context and the Mesop context.

3.  **Redirect to Home:** The `/__/auth/` endpoint then issues a `RedirectResponse` to the application's home page (`/home`). Crucially, it also sets the `session_id` cookie on this response, ensuring it will be available for all subsequent requests.

4.  **Mesop State Hydration (`on_load`):** When the Mesop page loads, its `on_load` event handler reads the `user_email` and `session_id` from the global `app.state` and uses them to populate the Mesop-specific `AppState`. This correctly "hydrates" the UI with the authenticated user and session information.

This pattern is the established and correct way to handle authentication in this application. It is robust, scalable, and correctly separates the concerns of the two frameworks.

## Configuration-Driven Architecture

A key architectural principle in this project is the use of centralized, type-safe configuration to drive the behavior of the UI and backend logic. This approach makes the application more robust, easier to maintain, and less prone to bugs.

A prime example of this is the handling of the VEO and Imagen models. Instead of hardcoding model names, capabilities, and constraints throughout the application, we define them in a single location:

-   **`config/veo_models.py`**
-   **`config/imagen_models.py`**

These files contain `dataclass` definitions that serve as a **single source of truth** for each model's properties, such as:

-   Supported aspect ratios
-   Valid video durations (min, max, and default)
-   Maximum number of samples
-   Supported generation modes (e.g., `t2v`, `i2v`, `interpolation`)

The UI components then read from these configuration objects to dynamically build the user interface. For example, the model selection dropdowns, sliders, and feature toggles are all populated and configured based on the capabilities of the currently selected model. This means that to add a new model or update an existing one, you only need to modify the relevant configuration file, and the entire application will adapt automatically.

This pattern is the preferred way to manage model capabilities and other complex configurations in this project.

## Testing Strategy

This project uses a combination of unit tests and integration tests to ensure code quality and reliability. The tests are located in the `test/` directory and are built using the `pytest` framework.

### Unit Tests

Unit tests are used to verify the internal logic of individual functions and components in isolation. They are fast, reliable, and do not depend on external services. We use mocking to simulate the behavior of external APIs, allowing us to test our code's logic without making real network calls.

### Integration Tests

Integration tests are used to verify the interaction between our application and live Google Cloud services. These tests make real API calls and are essential for confirming that our code can successfully communicate with the VEO and Imagen APIs.

-   **Marker:** Integration tests are marked with the `@pytest.mark.integration` decorator.
-   **Execution:** These tests are skipped by default. To run them, use the `-m` flag:
    ```bash
    pytest -m integration -v -s
    ```

### Component-Level Tests

For testing the data flow within our components (e.g., from a successful API call to the Firestore logging), we use component-level integration tests. These tests mock the external API calls but let the internal data handling and state management logic run as it normally would. This is a powerful way to catch bugs in our data mapping and event handling logic.

### Test Configuration

Tests that require access to Google Cloud Storage can be configured to use a custom GCS bucket via the `--gcs-bucket` command-line option. See the `test/README.md` file for more details.

## How to Add a New Page

Adding a new page to the application is a straightforward process. Here are the steps:

### Step 1: Create the Page File

Create a new Python file in the `pages/` directory. The name of the file should be descriptive of the page's purpose (e.g., `my_new_page.py`).

In this file, define a function that will contain the UI for your page. This function should accept the application state as an argument.

**`pages/my_new_page.py`:**
```python
import mesop as me
from state.state import AppState
from components.header import header
from components.page_scaffold import page_frame, page_scaffold

def my_new_page_content(app_state: AppState):
    with page_scaffold():
        with page_frame():
            header("My New Page", "rocket_launch")
            me.text("Welcome to my new page!")
```

### Step 2: Register the Page in `main.py`

Next, you need to register your new page in `main.py` so that the application knows how to serve it.

1.  Import your new page function at the top of `main.py`:
    ```python
    from pages.my_new_page import my_new_page_content
    ```

2.  Add a new `@me.page` decorator to define the route and other page settings:
    ```python
    @me.page(
        path="/my_new_page",
        title="My New Page - GenMedia Creative Studio",
        on_load=on_load,
    )
    def my_new_page():
        my_new_page_content(me.state(AppState))
    ```

### Step 3: Add the Page to the Navigation

To make your new page accessible to users, you need to add it to the side navigation.

1.  Open the `config/navigation.json` file.
2.  Add a new JSON object to the `pages` array for your new page. Make sure to give it a unique `id`.

**`config/navigation.json`:**
```json
{
  "pages": [
    // ... other pages ...
    {
      "id": 60, // Make sure this ID is unique
      "display": "My New Page",
      "icon": "rocket_launch",
      "route": "/my_new_page",
      "group": "workflows"
    }
  ]
}
```

### Step 4: (Optional) Control with a Feature Flag

If you want to control the visibility of your new page with an environment variable, you can add a `feature_flag` to its entry in `navigation.json`.

```json
{
  "id": 60,
  "display": "My New Page",
  "icon": "rocket_launch",
  "route": "/my_new_page",
  "group": "workflows",
  "feature_flag": "MY_NEW_PAGE_ENABLED"
}
```

Now, the "My New Page" link will only appear in the navigation if the `MY_NEW_PAGE_ENABLED` environment variable is set to `True` in your `.env` file.

That's it! When you restart the application, your new page will be available at the route you defined and will appear in the side navigation.

### How to Use the `library_chooser_button` Component

The `library_chooser_button` is a reusable component that allows users to select an image from the library as an input. Here is how to use it on a page:

1.  **Import the component and its event type:**
    ```python
    from components.library.library_chooser_button import library_chooser_button
    from components.library.events import LibrarySelectionChangeEvent
    ```

2.  **Define a callback handler:** Create a generator function on your page to handle the selection event. This function will receive the `LibrarySelectionChangeEvent` object, which contains the `gcs_uri` of the selected image and the `chooser_id` of the button that was clicked.

    *   **For a single chooser button on a page:**
        ```python
        def on_image_select(e: LibrarySelectionChangeEvent):
            state = me.state(YourPageState)
            state.your_image_field = e.gcs_uri
            yield
        ```

    *   **For multiple chooser buttons on the same page:**
        ```python
        def on_image_select(e: LibrarySelectionChangeEvent):
            state = me.state(YourPageState)
            if e.chooser_id == "person_chooser":
                state.person_image_gcs = e.gcs_uri
            elif e.chooser_id == "product_chooser":
                state.product_image_gcs = e.gcs_uri
            yield
        ```

3.  **Instantiate the component:** Call the component in your page's UI logic, passing the callback handler to the `on_library_select` prop. You must provide a unique `key` if you have multiple choosers on the same page.
    ```python
    # For a single chooser
    library_chooser_button(
        key="my_unique_chooser_key",
        on_library_select=on_image_select,
        button_label="Select from Library"
    )
    ```

## Key Takeaways from the VTO Page Development

- **GCS URI Handling:** This is a critical and recurring theme. The `common.storage.store_to_gcs` function returns a **full** GCS URI (e.g., `gs://your-bucket/your-object.png`). When using this value, you must be careful not to prepend the `gs://` prefix or the bucket name again. Doing so will create an invalid path and lead to "No such object" errors.
    - **For API Calls:** Pass the GCS URI returned from `store_to_gcs` directly to the API.
    - **For Displaying in Mesop:** To create a public URL for the `me.image` component, use the `.replace("gs://", "https://storage.mtls.cloud.google.com/")` method on the full GCS URI.

- **Displaying GCS Images:** The `me.image` component requires a public HTTPS URL, not a `gs://` URI. To display images from GCS, replace `gs://` with `https://storage.mtls.cloud.google.com/`.

- **State Management:** Avoid using mutable default values (like `[]`) in your state classes. Instead, use `field(default_factory=list)` to ensure that a new list is created for each user session.

- **UI Components:** If a component doesn't support a specific parameter (like `label` on `me.slider`), you can often achieve the same result by wrapping it in a `me.box` and using other components (like `me.text`) to create the desired layout.

- **Generator Functions:** When working with generator functions (those that use `yield`), make sure to include a `yield` statement after updating the state to ensure that the UI is updated.

## Key Takeaways from the Veo Model Refactor

- **SDK Type Specificity:** The `google-genai` SDK requires different `types` for different kinds of image-based video generation. Using the wrong type will result in a Pydantic validation error. The key is to be precise:
    - For a standard **Image-to-Video** call (one input image), the image must be wrapped in `types.Image(gcs_uri=..., mime_type=...)`.
    - For **Interpolation** (a first and last frame), both images must also be wrapped in `types.Image(gcs_uri=..., mime_type=...)`. The first frame is passed as the main `image` parameter, and the last frame is passed as the `last_frame` parameter inside the `GenerateVideosConfig`.

- **Configuration-Driven Lookups:** When a feature (like the Motion Portraits page) needs to get configuration for a model, it's crucial to use the correct key. Our `config/veo_models.py` uses a short version string (e.g., `"2.0"`) as the key, not the full model ID (e.g., `"veo-2.0-generate-001"`). Passing the wrong identifier will lead to an "Unsupported model" error. Always ensure the UI state provides the simple version string for lookups.

- **Isolating and Removing Legacy Code:** A major source of our errors was the presence of an old, non-SDK-based function (`generate_video_aiplatform`) that was still being called by one of the pages. This highlights the importance of completely removing obsolete code after a refactor to prevent it from being used accidentally. A single, unified function (`generate_video`) that handles all generation paths is much easier to maintain and debug.

- **Enhanced Error Logging:** When polling a long-running operation from the `google-genai` SDK, the `operation.error` attribute contains a detailed error message if the operation fails. It is critical to log this specific message in the exception handler. Relying on a generic error message hides the root cause and makes debugging significantly harder.

### Adding a New Field to a Generation Page

Adding a new parameter or field (like a negative prompt or a quality setting) to a generation page (e.g., Imagen, Veo) requires touching multiple files across the application stack. This guide outlines the data lifecycle you must consider.

Follow this checklist to ensure your feature is fully integrated:

1.  **State (`state/`):** Add your new field to the appropriate state class (e.g., `VeoState`). This is where the UI will store the user's input.
2.  **UI (`pages/`):** Add the UI control (e.g., `me.textarea`, `me.slider`) to the main page file (e.g., `pages/veo.py`) and create its corresponding event handler.
3.  **Request Schema (`models/requests.py`):** Update the request class (e.g., `VideoGenerationRequest`) to include your new field. This creates a clean data contract for the model layer.
4.  **Model Logic (`models/`):** Update the core generation function (e.g., `models/veo.py`) to use the new field from the request object and pass it to the underlying generative API.
5.  **Save to Firestore (`common/metadata.py` & `pages/`):**
    *   First, add the field to the `MediaItem` dataclass in `common/metadata.py`.
    *   Then, in the page's `on_click` handler (e.g., `on_click_veo`), ensure you populate this new field when creating the `MediaItem` to be logged.
6.  **Load from Firestore (`pages/library.py`):**
    *   This is a critical and easily missed step. In `pages/library.py`, find the `get_media_for_page` function.
    *   Update the `MediaItem` constructor inside this function to read your new field from the `raw_item_data` dictionary.
7.  **Display in Library (`pages/library.py`):** Update the details dialog within the library page to display the new field from the `MediaItem` object.
8.  **Handle Edge Cases:** Remember to update any related functionality. For example, does the "Clear" button on the page need to reset your new field?