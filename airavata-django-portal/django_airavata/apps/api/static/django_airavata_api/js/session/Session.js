class Session {
  init({ username, airavata_internal_user_id, is_gateway_admin = false }) {
    this.username = username;
    this.airavata_internal_user_id = airavata_internal_user_id;
    this.is_gateway_admin = is_gateway_admin;
  }
}

const session = new Session();
if (window.AiravataPortalSessionData) {
  // Initialize portal session object with data provided by base.html template
  session.init(window.AiravataPortalSessionData);
}

export default session;
