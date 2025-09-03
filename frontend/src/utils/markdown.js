/**
 * Markdown utility functions for parsing headings and section navigation
 */

/**
 * Parse markdown text and extract sections based on headings
 * @param {string} text - The markdown text to parse
 * @returns {Array} Array of section objects with title, level, start, and end positions
 */
export function parseMarkdownSections(text) {
  if (!text) return []
  
  const lines = text.split('\n')
  const sections = []
  let currentSection = null
  
  lines.forEach((line, index) => {
    const trimmedLine = line.trim()
    const headingMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/)
    
    if (headingMatch) {
      // Close previous section
      if (currentSection) {
        currentSection.end = index - 1
        sections.push(currentSection)
      }
      
      // Start new section
      const level = headingMatch[1].length
      const title = headingMatch[2]
      
      currentSection = {
        title,
        level,
        start: index,
        end: lines.length - 1, // Will be updated when next section starts
        lineNumber: index + 1, // 1-based line numbering
        headingText: trimmedLine
      }
    }
  })
  
  // Add the last section if it exists
  if (currentSection) {
    sections.push(currentSection)
  }
  
  return sections
}

/**
 * Find the current section based on a line number
 * @param {Array} sections - Array of section objects
 * @param {number} currentLine - Current line number (0-based)
 * @returns {Object|null} Current section object or null if not found
 */
export function getCurrentSection(sections, currentLine) {
  return sections.find(section => 
    currentLine >= section.start && currentLine <= section.end
  ) || null
}

/**
 * Get the next section after the current line
 * @param {Array} sections - Array of section objects
 * @param {number} currentLine - Current line number (0-based)
 * @returns {Object|null} Next section object or null if not found
 */
export function getNextSection(sections, currentLine) {
  const currentSection = getCurrentSection(sections, currentLine)
  if (!currentSection) {
    // If not in a section, find the first section after current line
    return sections.find(section => section.start > currentLine) || null
  }
  
  const currentIndex = sections.indexOf(currentSection)
  return currentIndex < sections.length - 1 ? sections[currentIndex + 1] : null
}

/**
 * Get the previous section before the current line
 * @param {Array} sections - Array of section objects
 * @param {number} currentLine - Current line number (0-based)
 * @returns {Object|null} Previous section object or null if not found
 */
export function getPreviousSection(sections, currentLine) {
  const currentSection = getCurrentSection(sections, currentLine)
  if (!currentSection) {
    // If not in a section, find the last section before current line
    const sectionsBeforeLine = sections.filter(section => section.start < currentLine)
    return sectionsBeforeLine.length > 0 ? sectionsBeforeLine[sectionsBeforeLine.length - 1] : null
  }
  
  const currentIndex = sections.indexOf(currentSection)
  return currentIndex > 0 ? sections[currentIndex - 1] : null
}

/**
 * Calculate character position for a given line number in text
 * @param {string} text - The full text
 * @param {number} lineNumber - Line number (0-based)
 * @returns {number} Character position
 */
export function getCharacterPositionForLine(text, lineNumber) {
  const lines = text.split('\n')
  let position = 0
  
  for (let i = 0; i < Math.min(lineNumber, lines.length); i++) {
    position += lines[i].length + 1 // +1 for newline character
  }
  
  return position
}

/**
 * Generate a table of contents from sections
 * @param {Array} sections - Array of section objects
 * @returns {Array} Array of TOC items with title, level, and lineNumber
 */
export function generateTableOfContents(sections) {
  return sections.map(section => ({
    title: section.title,
    level: section.level,
    lineNumber: section.lineNumber,
    start: section.start
  }))
}