const BARE_URL_PATTERN = /^https?:\/\/\S+$/i;

export function isBareUrl(content: string): boolean {
  return BARE_URL_PATTERN.test(content.trim());
}
