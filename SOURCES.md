# Official references

Reviewed while preparing version 0.1.0 on 2026-09-27. These are implementation
references, not claims that the project is endorsed by the linked organizations.
The code and documentation are original; APIs are used rather than copying
third-party implementations.

| Source | How it informed the project |
| --- | --- |
| [psutil API documentation](https://psutil.io/api/) | CPU sampling, available-memory metrics, disk usage, interface state and Windows service APIs. The site may show development APIs; the dependency is constrained below version 8. |
| [psutil stable 7.x documentation](https://psutil.readthedocs.io/stable/) | Compatibility reference for the supported dependency series. |
| [Python subprocess](https://docs.python.org/3/library/subprocess.html) | Argument arrays without a shell; timeout handling and child cleanup. |
| [Python socket](https://docs.python.org/3/library/socket.html) | Address resolution and explicit TCP connections. |
| [Python html](https://docs.python.org/3/library/html.html) | Escaping externally sourced report content. |
| [systemd unit states](https://www.freedesktop.org/wiki/Software/systemd/dbus/) | Distinguishing load state, active state and transitional states. |
| [systemctl upstream manual source](https://github.com/systemd/systemd/blob/main/man/systemctl.xml) | Querying machine-readable service properties with `show`. |
| [GitHub: building and testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) | Workflow matrix, installing the project and running tests. |
| [GitHub: publish with Desktop](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-an-existing-project-to-github-using-github-desktop) | Publishing a local repository and choosing visibility. |
| [GitHub: add local source code](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github) | Optional command-line publication instructions. |

Thresholds and recommendations are project design choices, not values prescribed
by these sources. The tool reports observations; it does not claim to determine
root cause from a single measurement.
