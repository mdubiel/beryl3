/**
 * HTMX Autocomplete Combobox Component
 *
 * A reusable component for HTMX-powered autocomplete comboboxes.
 * Handles selection, form submission, and value clearing.
 *
 * Usage:
 * - Add data-combobox="unique-id" to your text input
 * - The component will automatically wire up event handlers
 *
 * Required HTML structure:
 * <input type="hidden" name="field_id" id="combobox-{id}-value" />
 * <input type="hidden" name="field_name" id="combobox-{id}-name" />
 * <input type="text" name="q" id="combobox-{id}-search" data-combobox="{id}" />
 * <div id="combobox-{id}-results" class="hidden"></div>
 *
 * Autocomplete results should call:
 * window.comboboxSelect('{id}', itemId, itemName);
 */

(function() {
    'use strict';

    const DEBUG = typeof window.DJANGO_DEBUG !== 'undefined' ? window.DJANGO_DEBUG : false;

    function log(...args) {
        if (DEBUG) {
            console.log('[Combobox]', ...args);
        }
    }

    /**
     * Select an item from the combobox and optionally submit the form
     * @param {string} comboboxId - The unique ID of the combobox
     * @param {string|number} itemId - The ID of the selected item
     * @param {string} itemName - The display name of the selected item
     */
    window.comboboxSelect = function(comboboxId, itemId, itemName) {
        log('Select called:', comboboxId, itemId, itemName);

        const valueEl = document.getElementById('combobox-' + comboboxId + '-value');
        const nameEl = document.getElementById('combobox-' + comboboxId + '-name');
        const searchEl = document.getElementById('combobox-' + comboboxId + '-search');
        const resultsEl = document.getElementById('combobox-' + comboboxId + '-results');

        if (!valueEl || !searchEl) {
            console.error('[Combobox] Required elements not found for:', comboboxId);
            return;
        }

        // Set values
        valueEl.value = itemId;
        searchEl.value = itemName;
        if (nameEl) {
            nameEl.value = itemName;
        }

        // Hide dropdown
        if (resultsEl) {
            resultsEl.classList.add('hidden');
        }

        // Check if this combobox should auto-submit
        const autoSubmit = searchEl.getAttribute('data-combobox-submit') === 'true';
        if (autoSubmit) {
            log('Auto-submitting form for:', comboboxId);
            const form = searchEl.closest('form');
            if (form) {
                // Use HTMX to submit if available
                if (typeof htmx !== 'undefined') {
                    htmx.trigger(form, 'submit');
                } else {
                    form.submit();
                }
            }
        }
    };

    /**
     * Clear the combobox values
     * @param {string} comboboxId - The unique ID of the combobox
     */
    window.comboboxClear = function(comboboxId) {
        log('Clear called:', comboboxId);

        const valueEl = document.getElementById('combobox-' + comboboxId + '-value');
        const nameEl = document.getElementById('combobox-' + comboboxId + '-name');
        const searchEl = document.getElementById('combobox-' + comboboxId + '-search');

        if (valueEl) valueEl.value = '';
        if (nameEl) nameEl.value = '';
        if (searchEl) searchEl.value = '';
    };

    /**
     * Initialize combobox input event handlers
     * Updates the hidden name field when user types manually
     */
    function initComboboxes() {
        document.querySelectorAll('[data-combobox]').forEach(function(input) {
            const comboboxId = input.getAttribute('data-combobox');
            log('Initializing combobox:', comboboxId);

            // Update hidden name field and clear ID when user types
            input.addEventListener('input', function(e) {
                const nameEl = document.getElementById('combobox-' + comboboxId + '-name');
                const valueEl = document.getElementById('combobox-' + comboboxId + '-value');

                // Update name field with current value
                if (nameEl) {
                    nameEl.value = e.target.value;
                }

                // Clear ID field (user is typing manually, not selecting)
                if (valueEl) {
                    valueEl.value = '';
                }
            });

            // Hide results on blur
            input.addEventListener('blur', function() {
                const resultsEl = document.getElementById('combobox-' + comboboxId + '-results');
                if (resultsEl) {
                    setTimeout(function() {
                        resultsEl.classList.add('hidden');
                    }, 200);
                }
            });
        });
    }

    /**
     * Highlight query text in autocomplete results
     * Call this after HTMX swaps in autocomplete results
     * @param {string} containerId - The ID of the results container
     * @param {string} query - The search query to highlight
     */
    window.comboboxHighlightQuery = function(containerId, query) {
        const container = document.getElementById(containerId);
        if (!container || !query) return;

        container.querySelectorAll('[data-combobox-item-name]').forEach(function(span) {
            const name = span.getAttribute('data-combobox-item-name');
            if (name) {
                // Escape special regex characters
                const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp('(' + escapedQuery + ')', 'gi');
                const highlighted = name.replace(regex, '<strong>$1</strong>');
                span.innerHTML = highlighted;
            }
        });
    };

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initComboboxes);
    } else {
        initComboboxes();
    }

    // Re-initialize after HTMX swaps (for dynamically loaded content)
    document.body.addEventListener('htmx:afterSwap', function(event) {
        initComboboxes();
    });

})();
