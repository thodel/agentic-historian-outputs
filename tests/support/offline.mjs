// Browser tests read local fixtures; nothing they render may wait on the internet.
//
// 27.10.2026: e-codices.unifr.ch stopped answering. The fixture document
// "fixture-mit-quelle" shows its source's thumbnail from there, and a page's
// "load" event waits for every image — so 25 behavioural cases and one
// integration case timed out on a page that had rendered completely, and
// neither the site nor the change under test had anything to do with it.
// Requests that leave this machine are answered at once with a network error,
// as an offline reader would see them: the page still loads, and an image
// from elsewhere stays an image that did not arrive.

const LOCAL_HOSTS = new Set(["127.0.0.1", "localhost", "[::1]"]);

export function isExternal(url) {
  return (url.protocol === "http:" || url.protocol === "https:")
    && !LOCAL_HOSTS.has(url.hostname);
}

/** Abort every request ``target`` (a page or a context) sends off this machine. */
export async function offline(target) {
  await target.route(isExternal, route => route.abort("internetdisconnected"));
  return target;
}
