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
- [x] figure out InfluxDB 
- [x] Go through Librarian and check whether any of the events can be extended further
- [x] Split out smartapp into its own Python package
- [ ] Write documentation and publish code
- [ ] Get server running on mercury and writing to InfluxDB on venus
- [ ] See whether it's possible to get weather events to track outdoor temps along with indoor
