from humanoid_bot.platform import LinuxBackend, get_backend


def test_backend_selection_non_windows() -> None:
    backend = get_backend()
    # In the Linux build container we always get the fallback backend.
    assert isinstance(backend, LinuxBackend)


def test_linux_backend_interface() -> None:
    backend = LinuxBackend()
    assert backend.autostart_enabled() is False
    backend.set_autostart(False)  # no-op, must not raise
