# PDF-rendering av nästlade punktlistor

Problemet åtgärdades i PDF-renderingen, inte genom att ändra manusets markdownstruktur.

Korrekt markdown ska bevaras:

```md
- **Misstag: Att behandla all jord likadant.**
  - Varför det händer: Gödselråd skrivs ofta generellt.
  - Hur du undviker det: Anpassa mängd och metod efter jordtyp.
```

I den skapade PDF:en renderas rader med två inledande mellanslag och `-` som indenterade underpunkter.

Verifiering:
- PDF renderades till bildfiler.
- Underpunkterna har större vänsterindrag än huvudpunkterna.
- Manusets nästlade listor har inte plattats ut.
