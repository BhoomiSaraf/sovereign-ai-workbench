import { useEffect, useRef, useState } from 'react'
import { getHealth } from '../api/client'
import type { HealthResponse } from '../api/types'

interface UseHealthResult {
  health: HealthResponse | null
  error: string | null
  loading: boolean
}

// Polls GET /health so the sovereignty monitor and top bar reflect the
// backend's real state instead of a static snapshot.
export function useHealth(intervalMs = 5000): UseHealthResult {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const mounted = useRef(true)

  useEffect(() => {
    mounted.current = true

    async function poll() {
      try {
        const result = await getHealth()
        if (mounted.current) {
          setHealth(result)
          setError(null)
        }
      } catch (err) {
        if (mounted.current) {
          setError(err instanceof Error ? err.message : 'Failed to reach backend')
        }
      } finally {
        if (mounted.current) setLoading(false)
      }
    }

    poll()
    const id = setInterval(poll, intervalMs)

    return () => {
      mounted.current = false
      clearInterval(id)
    }
  }, [intervalMs])

  return { health, error, loading }
}
