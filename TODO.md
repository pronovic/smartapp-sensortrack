# TODO:

- [x] Unit test code in `dispatcher.py`
- [x] Add to_yaml() and from_yaml() on `LifecycleConverter`
- [x] Unit tests for serializing and deserializating `SmartAppDefinition`
- [x] Figure out where to add Python logging under `smartapp`
- [x] Wire up FastAPI to accept requests and forward to dispatcher
- [x] Create a dummy SmartApp and start integration testing the full flow
- [x] Capture digital signature data from the integration test messages
- [x] Implement digital signature checking, initially for only RSA-SHA256
- [x] Write unit tests for event handler
- [x] write unit tests for smartthings API
- [ ] figure out InfluxDB 
- [ ] Go through Librarian and check whether any of the events can be extended further
- [ ] Split out smartapp into its own Python package
