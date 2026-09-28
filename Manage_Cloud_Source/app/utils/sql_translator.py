import re

class SQLTranslator:
    """
    Translates SQL dialects and modernizes syntax for MySQL compatibility.
    """
    
    @staticmethod
    def translate(sql: str) -> str:
        if not sql:
            return sql
            
        # 1. Translate GETDATE() and SYSDATETIME() to NOW()
        sql = re.sub(r'\bGETDATE\s*\(\s*\)', 'NOW()', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bSYSDATETIME\s*\(\s*\)', 'NOW()', sql, flags=re.IGNORECASE)
        
        # 2. Translate TOP (n) to LIMIT n (Simplified, only handles simple TOP at start)
        # SQL Server: SELECT TOP 10 * FROM ...
        # MySQL: SELECT * FROM ... LIMIT 10
        top_match = re.search(r'SELECT\s+TOP\s+(\d+)\s+', sql, flags=re.IGNORECASE)
        if top_match:
            limit_val = top_match.group(1)
            sql = re.sub(r'SELECT\s+TOP\s+\d+\s+', 'SELECT ', sql, count=1, flags=re.IGNORECASE)
            if 'LIMIT' not in sql.upper():
                sql = sql.rstrip(';') + f" LIMIT {limit_val};"

        # 3. Translate ISNULL(col, val) to IFNULL(col, val)
        sql = re.sub(r'\bISNULL\s*\(', 'IFNULL(', sql, flags=re.IGNORECASE)
        
        # 4. Translate LEN(str) to LENGTH(str)
        sql = re.sub(r'\bLEN\s*\(', 'LENGTH(', sql, flags=re.IGNORECASE)
        
        # 5. Translate [identifier] to `identifier`
        sql = re.sub(r'\[([^\]]+)\]', r'`\1`', sql)
        
        # 6. Handle GO statements (common in SQL Server scripts)
        sql = re.sub(r'^\s*GO\s*$', ';', sql, flags=re.MULTILINE | re.IGNORECASE)
        
        # 7. Identity to Auto_Increment
        sql = re.sub(r'\bIDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)', 'AUTO_INCREMENT', sql, flags=re.IGNORECASE)

        return sql

    @staticmethod
    def split_statements(sql: str):
        """
        Splits a multi-statement SQL script into individual statements.
        Handles semicolons within quotes, various comment styles, and DELIMITER changes.
        """
        statements = []
        current_stmt = []
        
        i = 0
        n = len(sql)
        in_quote = False
        quote_char = None
        in_line_comment = False
        in_block_comment = False
        current_delimiter = ';'
        
        while i < n:
            # 1. Handle DELIMITER change (MySQL specific client command)
            if not in_quote and not in_line_comment and not in_block_comment:
                # Look for DELIMITER keyword at start of line or after whitespace
                if i == 0 or sql[i-1] in ('\n', '\r', ' ', '\t'):
                    peek = sql[i:i+50]
                    delim_match = re.match(r'^\s*DELIMITER\s+(\S+)', peek, re.IGNORECASE)
                    if delim_match:
                        current_delimiter = delim_match.group(1)
                        # Skip the DELIMITER line
                        eol = sql.find('\n', i)
                        if eol == -1: i = n
                        else: i = eol + 1
                        continue

            char = sql[i]
            next_char = sql[i+1] if i + 1 < n else ""
            
            # 2. Handle quotes
            if not in_line_comment and not in_block_comment:
                if char in ("'", '"', '`'):
                    if not in_quote:
                        in_quote = True
                        quote_char = char
                    elif quote_char == char:
                        # Check for escaping (MySQL uses \ or doubling for some, but \ is most common)
                        if i > 0 and sql[i-1] == '\\':
                            pass
                        else:
                            in_quote = False
                            quote_char = None
            
            # 3. Handle comments
            if not in_quote:
                if not in_block_comment and not in_line_comment:
                    if char == '-' and next_char == '-':
                        in_line_comment = True
                        i += 1 
                        continue
                    if char == '#':
                        in_line_comment = True
                        continue
                    if char == '/' and next_char == '*':
                        in_block_comment = True
                        i += 1
                        continue
                
                if in_line_comment and char == '\n':
                    in_line_comment = False
                
                if in_block_comment and char == '*' and next_char == '/':
                    in_block_comment = False
                    i += 2
                    continue

            # 4. Handle statement separator (dynamic delimiter)
            if not in_quote and not in_line_comment and not in_block_comment:
                delim_len = len(current_delimiter)
                if sql[i:i+delim_len] == current_delimiter:
                    # Found the current delimiter
                    # Do not include the delimiter itself in the sent statement if it's not ';'
                    # Actually, for MySQL, the trailing ';' is usually expected if it's the standard delim,
                    # but if it's a custom one like '//', the server doesn't want it at the end of the execute() call.
                    
                    stmt_str = "".join(current_stmt).strip()
                    if stmt_str:
                        statements.append(stmt_str)
                    current_stmt = []
                    i += delim_len
                    continue

            # 5. Build current statement
            if not in_line_comment and not in_block_comment:
                current_stmt.append(char)
            elif in_line_comment and char == '\n':
                current_stmt.append(char)
                
            i += 1
            
        # Add the last statement
        stmt_str = "".join(current_stmt).strip()
        if stmt_str:
            statements.append(stmt_str)
            
        return [s for s in statements if s]
