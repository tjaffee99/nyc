
// ====================================================================== Fine Hall
{
  const o = obb(FINE);
  // the tower stands at the western end of the base
  const westSign = Math.sin((o.bearing * Math.PI) / 180) > 0 ? -1 : 1; // sign of local y that points west
  const [tx, ty, td] = roomiest(FINE, o, (_x, y) => y * westSign > o.L * 0.1);
  const s = Math.min(8.5, td * 0.95);
  PRINCETON.push({
    id: 'pr_fine_hall',
    name: 'Fine Hall (mathematics tower)',
    kind: 'tower',
    built: [1966.5, 1970.2],
    end: 9999,
    anchor: FINE_ANCHOR,
    build: b => {
      block(b, FINE, 0, 11, '#8D8574', '#6F6B62');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // 170 ft (51.8 m) tower of ten floors on the three-storey base
        b.color('#99917F').box(tx, ty, 11, 2 * s, 2 * s, 40.816);
        b.color('#6F6B62').box(tx, ty, 51.816, 2 * s + 0.4, 2 * s + 0.4, 0.001);
        // continuous bands of windows read as dark strips
        for (let z = 14; z < 50; z += 3.6) b.color('#3F4A52').box(tx, ty, z, 2 * s + 0.12, 2 * s + 0.12, 1.4);
      });
    },
    replaces: [FINE],
    facts: {
      Built: 'commissioned 1966, occupied and dedicated 17 March 1970; Warner, Burns, Toan and Lunde; a long three-storey base topped by a tower of ten more floors, for the departments of mathematics and statistics',
      Height: 'the tower is 170 ft (51.8 m), 17 stories as counted by the university when it won the zoning variance of 1965',
      Model: 'plan is the real outline (Overture, 1,922 m2); the 170 ft height and the 3 + 10 floors are cited; the base height (11 m), the tower\'s plan and its place at the western end are estimated'
    },
    sources: [MUSEUM + 'artifact/80804cbc-2146-4bad-913c-12a3569d090d', MUSEUM + 'reference/188787d5-d55e-4260-97ed-5c54f37a70ad', OVERTURE]
  });
}

// ====================================================================== Jadwin Gymnasium
{
  const o = obb(JADWIN);
  PRINCETON.push({
    id: 'pr_jadwin_gymnasium',
    name: 'Jadwin Gymnasium',
    kind: 'stadium',
    built: [1964.5, 1969.4],
    end: 9999,
    anchor: JADWIN_ANCHOR,
    build: b => {
      block(b, JADWIN, 0, 8, '#9A958B', '#7B7870');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // three interlocking shells of unequal height over the arena
        const bw = (o.W * 0.86) / 3;
        const rise = [10, 7, 4.5];
        b.color('#8E918F');
        for (let i = 0; i < 3; i++) vault(b, -o.W * 0.43 + bw * (i + 0.5), 0, bw, o.L * 0.82, 8, rise[i]);
      });
    },
    replaces: [JADWIN],
    facts: {
      Built: 'groundbreaking 1964, opened 1969, $6.5 million; Walker O. Cain & Associates; 250,000 sq ft on five levels; 6,854 seats',
      Roof: 'a roof of three interlocking shells',
      Model: 'plan is the real outline (Overture, 10,907 m2); the dates, seating and the three shells are cited; no height is published: the 8 m wall and the shells (18, 15 and 12.5 m) are estimated, and the shells are drawn as parabolic vaults'
    },
    sources: [WIKI + 'Jadwin_Gymnasium', OVERTURE]
  });
}

// ====================================================================== McCarter Theatre
{
  const o = obb(MCCARTER);
  const stageEnd = clearance(MCCARTER, ...toWorld(o, 0, o.L * 0.3)) > clearance(MCCARTER, ...toWorld(o, 0, -o.L * 0.3)) ? 1 : -1;
  PRINCETON.push({
    id: 'pr_mccarter_theatre',
    name: 'McCarter Theatre',
    kind: 'building',
    built: [1928, 1930.15],
    end: 9999,
    anchor: MCCARTER_ANCHOR,
    build: b => {
      block(b, MCCARTER, 0, 11, '#B0734F', '#5E5A55');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // auditorium roof
        b.color('#4F4C49').gable(0, -stageEnd * o.L * 0.1, o.W * 0.55, o.L * 0.5, 11, 5, true);
        // the stage house at one end
        b.color('#A66A49').box(0, stageEnd * o.L * 0.3, 11, o.W * 0.6, o.L * 0.3, 13);
        b.color('#5E5A55').box(0, stageEnd * o.L * 0.3, 24, o.W * 0.6 + 0.4, o.L * 0.3 + 0.4, 0.4);
      });
    },
    replaces: [MCCARTER],
    facts: {
      Opened: '21 February 1930 with the Triangle Club show The Golden Dog; Collegiate Gothic; a 40-foot proscenium stage (the Berlind Theatre of 2003 was added later)',
      Model: 'plan is the real outline (Overture, 2,945 m2, including the later additions); the opening date and style are cited; no height or architect was found: the 11 m wall, the auditorium roof, the 24 m stage house and its end are estimated; construction start (1928) is an estimate'
    },
    sources: [WIKI + 'McCarter_Theatre', MUSEUM + 'artifact/aef55632-fd7b-4d93-84ce-16e7f3eaadc3', OVERTURE]
  });
}

// ====================================================================== Whig Hall and Clio Hall
function temple(id: string, name: string, ring: V2[], anchor: V2, frontBearing: number, other: string) {
  const o = obb(ring);
  const fd = frontFrame(o, frontBearing);
  PRINCETON.push({
    id,
    name,
    kind: 'building',
    built: [1891, 1893],
    end: 9999,
    anchor,
    build: b => {
      const sc = 0.8;
      block(b, ring, 0, 9.6, '#E9E6DC', '#D9D5C8');
      b.frame(o.cx, o.cy, 0, frontBearing, () => {
        const wd = fd.width * sc;
        const dp = fd.depth * sc;
        b.color('#D4D0C2').box(0, 0, 9.6, wd, dp, 0.5);
        b.color('#C9C5B7').gable(0, 0, wd, dp, 10.1, 3.4, true);
        // Ionic portico on the front: six columns carrying the pediment
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, dp / 2 - 0.3, 0, 9.6, 6, 0.5);
        b.color('#E9E6DC').box(0, dp / 2 - 0.3, 9.9, wd, 1.6, 0.8);
      });
    },
    replaces: [ring],
    facts: {
      Built: 'marble Greek-revival temples of 1893 for the two literary societies (the Ionic form of a Greek temple, replacing wood-and-stucco buildings of 1838); Arthur Page Brown; Whig Hall and ' + other + ' are identical',
      Model: 'plan is the real outline; the date, material and style are cited; no height is published: the 9.6 m wall, the 3.4 m pediment, the six-column portico and the front (the two halls face each other) are estimated; construction start (1891) is an estimate'
    },
    sources: ['https://lostnewengland.com/2021/03/clio-and-whig-halls-princeton-new-jersey/', 'https://dspace.njstatelib.org/items/cd452971-f61c-432f-a2dd-ab49f3883507', OVERTURE]
  });
}
// Whig (east) faces west, Clio (west) faces east
temple('pr_whig_hall', 'Whig Hall', WHIG, WHIG_ANCHOR, 270, 'Clio Hall');
temple('pr_clio_hall', 'Clio Hall', CLIO, CLIO_ANCHOR, 90, 'Whig Hall');

// ====================================================================== Princeton University Art Museum
{
  const o = obb(ART);
  const holes = [ART_H0, ART_H1, ART_H2];
  PRINCETON.push({
    id: 'pr_art_museum',
    name: 'Princeton University Art Museum (2025)',
    kind: 'building',
    built: [2021.5, 2025.83],
    end: 9999,
    anchor: ART_ANCHOR,
    build: b => {
      block(b, ART, 0, 12.5, '#BDB29A', '#A59B86', holes);
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // nine interlocking pavilions: the taller ones as raised volumes over a 3 x 3 grid
        const hs = [5, 2.5, 4, 3, 6, 3.5, 4.5, 2.5, 5];
        let k = 0;
        for (let iy = 0; iy < 3; iy++) {
          for (let ix = 0; ix < 3; ix++, k++) {
            const x = (ix - 1) * (o.W / 3);
            const y = (iy - 1) * (o.L / 3);
            const [wx, wy] = toWorld(o, x, y);
            let d = clearance(ART, wx, wy);
            for (const h of holes) d = Math.min(d, -clearance(h, wx, wy));
            if (d < 5) continue;
            const s = Math.min(d * 0.9, o.W / 3 * 0.8);
            b.color(k % 2 ? '#C9BEA6' : '#AFA58E').box(x, y, 12.5, 2 * s, 2 * s, hs[k]);
          }
        }
      });
    },
    replaces: [ART],
    facts: {
      Built: 'construction began summer 2021 after the old museum was demolished; opened 31 October 2025; Adjaye Associates with Cooper Robertson; about 145,000 sq ft; three storeys of nine interlocking pavilions in alternating rough and polished stone',
      Model: 'plan is the real outline with its three courtyards (Overture, 7,474 m2); the dates, three storeys and nine pavilions are cited; no height is published: the 12.5 m body and the raised pavilion volumes (to 18 m) are estimated. The museum of 1890 / 1966 on this ground is not modelled'
    },
    sources: [WIKI + 'Princeton_University_Art_Museum', 'https://www.dezeen.com/2025/10/31/adjaye-associates-princeton-university-art-museum/amp/', OVERTURE]
  });
}

// ====================================================================== Nassau Presbyterian Church
{
  const o = obb(NPC);
  PRINCETON.push({
    id: 'pr_nassau_presbyterian',
    name: 'Nassau Presbyterian Church',
    kind: 'building',
    built: [1835, 1836.5],
    end: 9999,
    anchor: NPC_ANCHOR,
    build: b => {
      const fd = frontFrame(o, 0);
      block(b, NPC, 0, 9, '#E4DCC8', '#8F8A80');
      b.frame(o.cx, o.cy, 0, 0, () => {
        const wd = fd.width * 0.62;
        const dp = fd.depth * 0.8;
        // Greek Revival front to Nassau Street (north), pedimented, with a steeple behind the front
        b.color('#8F8A80').gable(0, 0, wd, dp, 9, 4.2, true);
        b.color('#EFEADB');
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, dp / 2 - 0.3, 0, 9, 4, 0.5);
        const ty = dp / 2 - 4.5;
        b.color('#E4DCC8').box(0, ty, 9, 5.6, 5.6, 11);
        b.color('#EFEADB').box(0, ty, 20, 4.8, 4.8, 5);
        b.color('#6F6B66');
        spire(b, 0, ty, 3.4, 25, 34, 8);
      });
    },
    replaces: [NPC],
    facts: {
      Built: 'the church burned in 1835 and its replacement was completed in 1836; Charles Steadman; Greek Revival in stuccoed brick (fires also in 1813)',
      Model: 'plan is the real outline (Overture, 1,748 m2, including later additions); the date, architect and style are cited; no height is published: the 9 m walls, the portico, the steeple (34 m) and its position are estimated; the front is assumed to face Nassau Street (north); construction start (1835) is an estimate'
    },
    sources: [WIKI + 'Nassau_Presbyterian_Church', WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}
