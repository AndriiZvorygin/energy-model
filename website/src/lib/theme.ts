export type ThemePreference = 'auto' | 'light' | 'dark'

export const isLocalNight = (date = new Date()) => {
  const hour = date.getHours()
  return hour < 7 || hour >= 19
}

export const resolveTheme = (preference: ThemePreference, date = new Date()) =>
  preference === 'auto' ? (isLocalNight(date) ? 'dark' : 'light') : preference

export const readThemePreference = (): ThemePreference => {
  const stored = localStorage.getItem('themePreference') ?? localStorage.getItem('theme')
  return stored === 'light' || stored === 'dark' ? stored : 'auto'
}
