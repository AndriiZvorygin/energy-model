export const decimal = (value: number | null | undefined, digits = 3) => value == null ? '—' : value.toFixed(digits)
export const percent = (value: number | null | undefined, digits = 1) => value == null ? '—' : `${(value * 100).toFixed(digits)}%`
export const numberValue = (value: number | null | undefined, digits = 1) => value == null ? '—' : value.toFixed(digits)
