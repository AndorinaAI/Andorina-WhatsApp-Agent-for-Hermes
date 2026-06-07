def paginate_output(text: str, max_chunk_size: int = 1500) -> list[str]:
    """Splits output into chunks safe for WhatsApp limits."""
    if not text:
        return []
        
    chunks = []
    while text:
        if len(text) <= max_chunk_size:
            chunks.append(text)
            break
            
        # Try to find a nice break point (newline or space)
        split_point = text.rfind('\n', 0, max_chunk_size)
        if split_point == -1:
            split_point = text.rfind(' ', 0, max_chunk_size)
            if split_point == -1:
                split_point = max_chunk_size
                
        chunks.append(text[:split_point].strip())
        text = text[split_point:].strip()
        
    return chunks
