export function getLocationParams(keys: string[]) {
    const temData = new URLSearchParams(window.location.search);
    return keys.map((key: string) => {
        return temData.get(key);
    });
}
