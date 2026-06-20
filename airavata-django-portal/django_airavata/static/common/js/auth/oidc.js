// Browser-side OpenID Connect (Authorization Code + PKCE) against Keycloak.
//
// The portal no longer runs the OIDC flow server-side: the browser obtains the
// Keycloak access token via the public `pga-public` client and sends it as a
// Bearer credential to the API. The token is also mirrored into a short-lived
// cookie (`kc_token`) so Django can authenticate top-level page navigations,
// which cannot carry an Authorization header. Django only *validates* the token
// (it is no longer an identity authority).
//
// Config is injected by base.html as `window.AiravataOidcConfig` from settings.

import { UserManager, WebStorageStateStore } from "oidc-client-ts";

const cfg = window.AiravataOidcConfig || {};

const userManager = new UserManager({
  authority: cfg.authority,
  client_id: cfg.clientId,
  redirect_uri: cfg.redirectUri || window.location.origin + "/",
  post_logout_redirect_uri: cfg.postLogoutRedirectUri || window.location.origin + "/",
  response_type: "code",
  scope: cfg.scope || "openid profile email",
  userStore: new WebStorageStateStore({ store: window.localStorage }),
  automaticSilentRenew: true,
  monitorSession: false,
});

// Cached access token for synchronous reads by FetchUtils (kept fresh by the
// userLoaded / silent-renew events and by ensureAuthenticated()).
let currentToken = null;

/** Synchronous access to the current token; null if not authenticated. */
export function getAccessTokenSync() {
  return currentToken;
}

// Mirror the access token into a cookie so server-rendered page loads can be
// authenticated by Django (SameSite=Lax, Secure on HTTPS). Cleared on logout.
function setTokenCookie(token) {
  currentToken = token;
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `kc_token=${token}; Path=/; SameSite=Lax${secure}`;
}
function clearTokenCookie() {
  currentToken = null;
  document.cookie = "kc_token=; Path=/; Max-Age=0; SameSite=Lax";
}

userManager.events.addUserLoaded((user) => setTokenCookie(user.access_token));
userManager.events.addUserUnloaded(() => clearTokenCookie());

export async function getUser() {
  return userManager.getUser();
}

export async function getAccessToken() {
  const user = await userManager.getUser();
  return user && !user.expired ? user.access_token : null;
}

export function login(returnTo) {
  return userManager.signinRedirect({
    state: { returnTo: returnTo || window.location.href },
  });
}

export async function logout() {
  clearTokenCookie();
  return userManager.signoutRedirect();
}

// Ensure a valid token before the app boots: complete the redirect callback,
// reuse/refresh a stored session, or redirect to Keycloak. Resolves to a valid
// access token, or never resolves (because it redirects) when login is needed.
export async function ensureAuthenticated() {
  const params = new URLSearchParams(window.location.search);
  if (params.has("code") && params.has("state")) {
    const user = await userManager.signinCallback();
    setTokenCookie(user.access_token);
    const returnTo = (user.state && user.state.returnTo) || window.location.origin + "/";
    window.history.replaceState({}, document.title, returnTo);
    return user.access_token;
  }

  let user = await userManager.getUser();
  if (user && !user.expired) {
    setTokenCookie(user.access_token);
    return user.access_token;
  }

  try {
    user = await userManager.signinSilent();
    if (user && !user.expired) {
      setTokenCookie(user.access_token);
      return user.access_token;
    }
  } catch (e) {
    // No silent session available; fall through to interactive login.
  }

  await login();
  return null;
}

export default userManager;
