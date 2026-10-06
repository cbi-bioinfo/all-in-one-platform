from lightning.pytorch.callbacks import Callback

from chemprop.utils.registry import ClassRegistry

CallbackRegistry = ClassRegistry[Callback]()

# NOTE (drug_dev_platform tox_pred/chemprop deviation): the optional `myerson`
# explainability package is not installed (see pyproject.toml's dependency
# notes) since its pinned version doesn't resolve on this platform's PyPI
# mirror and it's only used by this one optional callback, which our
# train/serve contract never invokes. Upstream imports it unconditionally
# here, which would break `import chemprop` (and therefore the whole `chemprop`
# CLI, since chemprop.cli.main -> ... -> chemprop.callbacks) entirely without
# it. Import it lazily instead so the rest of the package works normally;
# only actually requesting the "myerson" callback will raise ImportError.
try:
    from .interpret import MyersonExplainerCallback  # noqa: E402 # avoid circular import

    __all__ = ["CallbackRegistry", "MyersonExplainerCallback"]
except ImportError:
    __all__ = ["CallbackRegistry"]
