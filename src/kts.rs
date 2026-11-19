use base::config::keys;
use hbb_common::config;

include!("../kts/generated/client.rs");

pub fn init() {
    *config::APP_NAME.write().unwrap() = APP_NAME.to_owned();
    *config::PROD_RENDEZVOUS_SERVER.write().unwrap() = ID_SERVER.to_owned();
    {
        let mut settings = config::OVERWRITE_SETTINGS.write().unwrap();
        for (key, value) in [
            (keys::OPTION_CUSTOM_RENDEZVOUS_SERVER, ID_SERVER),
            (keys::OPTION_RELAY_SERVER, RELAY_SERVER),
            (keys::OPTION_KEY, PUBLIC_KEY),
            (keys::OPTION_API_SERVER, ""),
            (keys::OPTION_ALLOW_AUTO_UPDATE, "N"),
        ] {
            settings.insert(key.to_owned(), value.to_owned());
        }
    }
    config::DEFAULT_SETTINGS
        .write()
        .unwrap()
        .insert(keys::OPTION_APPROVE_MODE.to_owned(), "click".to_owned());
    config::OVERWRITE_LOCAL_SETTINGS
        .write()
        .unwrap()
        .insert(keys::OPTION_ENABLE_CHECK_UPDATE.to_owned(), "N".to_owned());
}
