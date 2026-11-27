"""Google (OpenID Connect) login gate.

Uses Streamlit's built-in authentication (``st.login`` / ``st.logout`` /
``st.user``), which talks to Google's official OIDC endpoints. Only the
accounts listed in ``ALLOWED_EMAILS`` are allowed to use the app.

The gate activates as soon as the ``[auth]`` credentials are present (on Render
these are written to ``.streamlit/secrets.toml`` by ``start.sh`` from the
``GOOGLE_CLIENT_ID`` / ``GOOGLE_CLIENT_SECRET`` environment variables), or when
``NANOPRO_AUTH_ENABLED`` is set explicitly. While no credentials exist the app
runs normally, so the Streamlit Community Cloud deployment is unaffected.
"""

import os

import streamlit as st

# Only these Google accounts may open the studio.
ALLOWED_EMAILS = {
    "mangeshbagul15@gmail.com",
    "nanoproaistudio@gmail.com",
}


def _auth_configured() -> bool:
    """True when the ``[auth]`` block is present in Streamlit secrets."""
    try:
        return "auth" in st.secrets and bool(st.secrets["auth"])
    except Exception:
        return False


def _user_info() -> dict:
    """Safe snapshot of ``st.user`` as a plain dict.

    ``st.user`` raises ``AttributeError`` for missing claims, so we read the
    underlying mapping instead of accessing attributes directly.
    """
    try:
        return dict(st.user.to_dict())
    except Exception:
        try:
            return dict(st.user)
        except Exception:
            return {}


def auth_enabled() -> bool:
    """Whether the Google login gate should be enforced.

    Returns True only when the gate is actually usable: either the ``[auth]``
    credentials are configured, or it was switched on explicitly. This keeps the
    app fully functional while the Google credentials are still being set up.
    """
    if _auth_configured():
        return True
    if os.getenv("NANOPRO_AUTH_ENABLED", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return False


def enforce_login() -> None:
    """Show the Google sign-in page and stop the script for anyone not allowed."""
    if not auth_enabled():
        return

    if not _auth_configured():
        st.error(
            "🔒 Login is required but the Google OAuth credentials are not "
            "configured on this server. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET, AUTH_REDIRECT_URI and AUTH_COOKIE_SECRET."
        )
        st.stop()

    info = _user_info()
    if not info.get("is_logged_in"):
        _render_sign_in()
        st.stop()

    email = (info.get("email") or "").strip().lower()
    if email not in ALLOWED_EMAILS:
        _render_denied(email)
        st.stop()

    _render_signed_in_badge(email)


def _render_sign_in() -> None:
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    st.markdown(
        "<h1 style='text-align:center'>🎬 NanoPro Reel Maker</h1>"
        "<p style='text-align:center;color:#94A3B8;font-size:1.05rem'>"
        "Studio access is restricted to authorized Google accounts.<br>"
        "Please sign in to continue.</p>",
        unsafe_allow_html=True,
    )
    _c1, c2, _c3 = st.columns([1, 1, 1])
    with c2:
        # st.login() redirects to Google's official consent screen, where the
        # browser shows its own "Save password" option and password eye toggle.
        st.button(
            "🔐 Sign in with Google",
            on_click=st.login,
            width="stretch",
            type="primary",
        )


def _render_denied(email: str) -> None:
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    st.error(
        f"⛔ Access denied for **{email or 'this account'}**.\n\n"
        "This studio is restricted to specific accounts only."
    )
    _c1, c2, _c3 = st.columns([1, 1, 1])
    with c2:
        st.button("Switch Google account", on_click=st.logout, width="stretch")


def _render_signed_in_badge(email: str) -> None:
    with st.sidebar:
        st.caption(f"👤 Signed in as {email}")
        st.button("Sign out", on_click=st.logout, width="stretch")
