/**
 * useSidebar — shared sidebar collapsed state.
 * Using a module-level ref so all consumers share the same instance.
 */
import { ref } from 'vue'

const collapsed = ref(false)

export function useSidebar() {
  function toggle() {
    collapsed.value = !collapsed.value
  }

  return { collapsed, toggle }
}
