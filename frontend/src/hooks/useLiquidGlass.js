import { useEffect, useRef } from 'react'
import { liquidGlass } from '../lib/liquid-glass'

export function useLiquidGlass(options = {}) {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return undefined
    const instance = liquidGlass(ref.current, options)
    return () => instance.destroy()
  }, [])
  return ref
}
