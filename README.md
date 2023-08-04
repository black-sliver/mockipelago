# Mockipelago

An [Archipelago](https://github.com/ArchipelagoMW/Archipelago) mock server.
This is WIP and very incomplete.

## Usage

See [sample.py](sample.py).

## But why?

The goal is to be able to do automated testing of clients.

### Why not extend upstream MultiServer?

* Fewer dependencies -> faster startup
* Have the option to implement multiple versions/variants of the protocol in a single server

### Why not mock in the target application?

* Mocking something asynchronous is hard in some languages/frameworks
* The server can be shared between multiple targets
* Test cases can be shared between multiple targets
* We can copy code from and mimic behavior of MultiServer since both are python
* A mock server can be used for automated or semi-automated end-to-end tests (including the network stack)
