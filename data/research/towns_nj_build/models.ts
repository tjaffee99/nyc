
// ====================================================================== TRENTON
// ---------------------------------------------------------------------- Richard J. Hughes Justice Complex
{
  const o = obb(HUGHES);
  NJ_TOWNS.push({
    id: 'trn_hughes_justice',
    name: 'Richard J. Hughes Justice Complex',
    kind: 'building',
    built: [1979.5, 1982.5],
    end: 9999,
    anchor: HUGHES_ANCHOR,
    build: b => {
      block(b, HUGHES, 0, 30, '#A9A294', '#6E6A64');
      b.color('#8C877E').prism(HUGHES, 30, 30.9, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the cube that holds the court, rising out of the two eight-storey office wings
        const [x, y, d] = roomiest(HUGHES, o);
        const h = Math.min(d * 0.92, 21);
        b.color('#B9B2A4').box(x, y, 30, 2 * h, 2 * h, 41.62 - 30);
        b.color('#6E6A64').box(x, y, 41.55, 2 * h - 1, 2 * h - 1, 0.07);
      });
    },
    replaces: [HUGHES],
    facts: {
      Built: 'completed and dedicated 1982 (the Justice Center complex); modernist, eleven storeys, about 1,080,000 sq ft; two eight-storey office buildings around a cube that houses the court, an atrium lobby open through ten storeys',
      Model: 'plan is the real outline (Overture, 9,192 m2); the date, the eleven storeys and the height of 41.62 m (the cube) are cited; the 30 m of the office wings, the cube\'s side and its position (the roomiest point of the plan) and the colours are estimated; construction start (1979.5) is an estimate'
    },
    sources: [WIKI + 'Richard_J._Hughes_Justice_Complex', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Cathedral of St. Mary of the Assumption
{
  const o = obb(STMARY);
  NJ_TOWNS.push({
    id: 'trn_st_mary_cathedral',
    name: 'Cathedral of St. Mary of the Assumption',
    kind: 'building',
    built: [1957, 1959.2],
    end: 9999,
    anchor: STMARY_ANCHOR,
    build: b => {
      block(b, STMARY, 0, 10.5, '#B9A58B', '#7A6F63');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // nave under a gable roof; a modern Romanesque bell tower at the front end
        const [gw, gl] = fit(STMARY, o, 0, -o.L * 0.06, o.W * 0.72, o.L * 0.74);
        b.color('#7A6F63').gable(0, -o.L * 0.06, gw, gl, 10.5, 5.5, true);
        const [tx, ty, td] = roomiest(STMARY, o, (_x, y) => y > o.L * 0.22);
        const ts = Math.min(6.6, td * 1.25);
        b.color('#B9A58B').box(tx, ty, 0, ts, ts, 25.5);
        b.color('#8F8068').box(tx, ty, 25.5, ts + 0.6, ts + 0.6, 0.5);
        b.color('#6B6258');
        spire(b, tx, ty, ts * 0.7, 26, 29.87, 4);
      });
    },
    replaces: [STMARY],
    facts: {
      Built: 'church dedicated 1871, cathedral from 1881; the spire came down in early 1956 and a fire of 14 March 1956 destroyed it; the second cathedral was dedicated 14 March 1959 (a modern interpretation of the Romanesque); the bell tower rises 98 ft',
      Model: 'plan is the real outline (Overture, 1,640 m2); the dates and the 98 ft (29.87 m) tower are cited; the 10.5 m walls, the nave roof, the tower\'s corner and its cap are estimated, and which end is the front is a guess; construction start (1957) is an estimate. The church of 1871 is not modelled'
    },
    sources: [WIKI + 'Cathedral_of_St._Mary_of_the_Assumption_(Trenton,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Broad Street National Bank
{
  const o = obb(BANK);
  NJ_TOWNS.push({
    id: 'trn_broad_street_bank',
    name: 'Broad Street National Bank',
    kind: 'tower',
    built: [1899, 1900.5],
    end: 9999,
    anchor: BANK_ANCHOR,
    build: b => {
      block(b, BANK, 0, 10, '#B8AF9A', '#B8AF9A');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        b.color('#DCD6C6').box(0, 0, 10, o.W - 0.8, o.L - 0.8, 41.2);
        b.color('#C9C2AE').box(0, 0, 51.2, o.W + 0.6, o.L + 0.6, 1.4);
        b.color('#D2CBB8').box(0, 0, 52.6, o.W - 2.6, o.L - 2.6, 2.2);
        b.color('#8C8578').box(0, 0, 54.7, o.W - 2.6, o.L - 2.6, 0.1);
      });
    },
    replaces: [BANK],
    facts: {
      Built: 'built 1900, William A. Poland, Beaux Arts, a skyscraper; listed on the National Register 17 January 2008; stands at 143 East State Street beside the Motor Vehicles Building',
      Model: 'plan is the real outline (Overture, 2,199 m2, a rectangle); the date, architect and style are cited; no height is published: the 54.8 m top is the footprint\'s measured roof height, and the base, shaft, cornice and attic bands are estimated; construction start (1899) is an estimate'
    },
    sources: [WIKI + 'Broad_Street_National_Bank', WIKI + 'Downtown_Trenton_Commercial_Historic_District', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Mercer County Courthouse
{
  const o = obb(COURTHOUSE);
  NJ_TOWNS.push({
    id: 'trn_mercer_courthouse',
    name: 'Mercer County Courthouse',
    kind: 'building',
    built: [1902.4, 1903.5],
    end: 9999,
    anchor: COURTHOUSE_ANCHOR,
    build: b => {
      block(b, COURTHOUSE, 0, 19, '#D9D3C3', '#8A857B');
      b.color('#C7C0AE').prism(COURTHOUSE, 19, 20.2, {top: false});
      const [e0, e1] = extent(COURTHOUSE, o.cx, o.cy, 90);
      // front to Broad Street (east): a columned portico under a pediment
      b.frame(o.cx, o.cy, 0, 90, () => {
        const wd = Math.min(o.W, o.L) * 0.55;
        b.color('#EDE8DA');
        colonnade(b, -wd / 2 + 0.8, wd / 2 - 0.8, e1 - 0.3, 0, 17, 6, 0.55);
        b.color('#8A857B').gable(0, e1 - 1.3, wd, 3.2, 17, 2.6, true);
        // a central drum and dome: the measured roof reaches 27.1 m
        b.color('#D9D3C3').cylinder(0, 0, 7.5, 20.2, 23.2, 20, {top: false});
        b.color('#8FA79A').dome(0, 0, 7.5, 23.2, 3.9, 20, 5);
      });
      void e0;
    },
    replaces: [COURTHOUSE],
    facts: {
      Built: 'cornerstone laid 14 May 1902, the classical Beaux Arts building by William Slack replaced a Greek Revival courthouse that served until 1903; 209 South Broad Street; the Criminal Courthouse of 2013 stands behind',
      Model: 'plan is the real outline (Overture, 2,970 m2); the cornerstone, architect and style are cited; no height is published: the 27.1 m top is the footprint\'s measured roof height, taken here as a central drum and dome (the form is an estimate), and the 19 m walls, the east-facing portico and the colours are estimated; completion (1903.5) is an estimate'
    },
    sources: [WIKI + 'Mercer_County_Courthouse_(New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Trenton City Hall
{
  const o = obb(CITYHALL);
  NJ_TOWNS.push({
    id: 'trn_city_hall',
    name: 'Trenton City Hall',
    kind: 'building',
    built: [1907.5, 1910],
    end: 9999,
    anchor: CITYHALL_ANCHOR,
    build: b => {
      block(b, CITYHALL, 0, 15.5, '#E7E3D8', '#8C8A82');
      b.color('#D5D0C2').prism(CITYHALL, 15.5, 16.5, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // hipped roof over the main block, a columned centre
        const [hw, hl] = fit(CITYHALL, o, 0, 0, o.W * 0.86, o.L * 0.8);
        b.color('#7C9A86').hip(0, 0, hw, hl, 16.5, 4.7);
        b.color('#EFEBDF');
        colonnade(b, -o.L * 0.18, o.L * 0.18, o.W / 2 - 0.2, 0, 13.5, 6, 0.5);
      });
    },
    replaces: [CITYHALL],
    facts: {
      Built: 'designed 1907 by Spencer Roberts, opened to the public 1910; white marble, Renaissance; murals by Everett Shinn; listed on the National Register 30 January 1978',
      Model: 'plan is the real outline (Overture, 1,416 m2); the design year, opening, architect, style and material are cited; no height is published: the 21.2 m top is the footprint\'s measured roof height, reached by an estimated hipped roof over estimated 15.5 m walls; the columned centre and its side are estimated; construction start (1907.5) is an estimate'
    },
    sources: [WIKI + 'Trenton_City_Hall', WIKI + 'Trenton,_New_Jersey', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Roebling Machine Shop
{
  const o = obb(ROEBLING);
  NJ_TOWNS.push({
    id: 'trn_roebling_machine_shop',
    name: 'Roebling Machine Shop',
    kind: 'building',
    built: [1889.6, 1890.8],
    end: 9999,
    anchor: ROEBLING_ANCHOR,
    build: b => {
      block(b, ROEBLING, 0, 11, '#9B5B45', '#5E5953');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the high clerestory bay of a wire-rope machine shop
        const [gw, gl] = fit(ROEBLING, o, 0, 0, o.W * 0.5, o.L * 0.86);
        b.color('#5E5953').gable(0, 0, gw, gl, 11, 5.2, true);
      });
    },
    replaces: [ROEBLING],
    facts: {
      Built: 'built 1890 (further work 1901), the oldest surviving building of John A. Roebling\'s Sons Company in Chambersburg; listed on the National Register 4 September 1997; now a museum space',
      Model: 'plan is the real outline (Overture, 5,950 m2); the date is cited; no height is published: the 16.2 m top is the footprint\'s measured roof height, reached by an estimated clerestory gable over estimated 11 m brick walls; construction start (1889.6) is an estimate'
    },
    sources: [WIKI + 'Roebling_Machine_Shop', WIKI + 'Chambersburg,_Trenton,_New_Jersey', OVERTURE]
  });
}

// ---------------------------------------------------------------------- CURE Insurance Arena
{
  const o = obb(CURE);
  NJ_TOWNS.push({
    id: 'trn_cure_arena',
    name: 'CURE Insurance Arena (Sun National Bank Center)',
    kind: 'stadium',
    built: [1997.92, 1999.76],
    end: 9999,
    anchor: CURE_ANCHOR,
    build: b => {
      block(b, CURE, 0, 12, '#B7B3AB', '#8A8780');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the arena roof: a shallow barrel vault over the bowl
        b.color('#6F7A82');
        vault(b, 0, 0, o.W * 0.84, o.L * 0.8, 12, 6, 8);
        b.color('#C9C5BC').box(0, 0, 0, o.W * 0.2, o.L * 0.02, 0.01);
      });
    },
    replaces: [CURE],
    facts: {
      Built: 'groundbreaking 2 December 1997, opened 6 October 1999 as Sovereign Bank Arena (Sun National Bank Center 2009-2017, CURE Insurance Arena since); $53 million; Mercer County Improvement Authority; Trenton Titans / Devils until 2013',
      Model: 'plan is the real outline (Overture, 9,216 m2); the dates are cited; no height is published: the footprint\'s measured roof height is 11.9 m (an average over the building); the 12 m walls and the 6 m barrel roof (top 18 m) are estimated'
    },
    sources: [WIKI + 'CURE_Insurance_Arena', OVERTURE]
  });
}

// ====================================================================== NEW BRUNSWICK
// ---------------------------------------------------------------------- Johnson & Johnson World Headquarters
{
  const o = obb(JJ);
  NJ_TOWNS.push({
    id: 'nb_jj_headquarters',
    name: 'Johnson & Johnson World Headquarters',
    kind: 'tower',
    built: [1980, 1983.5],
    end: 9999,
    anchor: JJ_ANCHOR,
    build: b => {
      block(b, JJ, 0, 11.5, '#E3E8EA', '#C7CED2');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the white 16-storey tower of Pei Cobb Freed, standing up out of the three-storey modules
        const [x, y, d] = roomiest(JJ, o);
        const tw = Math.min(d * 1.5, 34);
        const tl = Math.min(d * 1.8, 46);
        b.color('#F1F4F5').box(x, y, 11.5, tw, tl, 70 - 11.5);
        b.color('#B9C3C8').box(x, y, 40, tw + 0.4, tl + 0.4, 0.6);
        b.color('#9AA5AB').box(x, y, 69.8, tw, tl, 0.2);
      });
    },
    replaces: [JJ],
    facts: {
      Built: 'opened 1983 (Wikipedia\'s infobox says completed 1982); Pei Cobb Freed and Partners (I. M. Pei took part in the plan); a 16-storey tower and seven connecting three-storey modules sheathed in glass and white enameled aluminum on a 12-acre site',
      Model: 'plan is the real outline of the whole complex (Overture, 6,346 m2); the opening year, the 16 storeys and the 70 m roof are cited; the tower\'s position and plan (the roomiest part of the outline), the 11.5 m modules and the band at the 9th storey are estimated; construction start (1980) is an estimate'
    },
    sources: [WIKI + 'Johnson_and_Johnson_Plaza', OVERTURE]
  });
}

// ---------------------------------------------------------------------- New Brunswick Performing Arts Center
{
  const o = obb(NBPAC);
  NJ_TOWNS.push({
    id: 'nb_performing_arts_center',
    name: 'New Brunswick Performing Arts Center',
    kind: 'tower',
    built: [2017.5, 2019.67],
    end: 9999,
    anchor: NBPAC_ANCHOR,
    build: b => {
      block(b, NBPAC, 0, 22, '#B3AFA6', '#8E8B84');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the residential tower above the theatres: 23 storeys in all
        const [x, y, d] = roomiest(NBPAC, o);
        const s = Math.min(d * 1.7, 34);
        b.color('#C5CED3').box(x, y, 22, s, s * 1.1, 89.61 - 22);
        b.color('#8E99A0').box(x, y, 89.3, s, s * 1.1, 0.31);
      });
    },
    replaces: [NBPAC],
    facts: {
      Built: 'construction began 2017, completed 2019, officially opened 4 September 2019; US$172 million, 23 storeys (18 of them residential, 207 apartments, 30,000 sq ft of offices); Elkus Manfredi Architects; two theatres and rehearsal studios beside the State Theatre',
      Model: 'plan is the real outline (Overture, 2,694 m2); the dates, 23 storeys and the 89.61 m roof are cited; the 22 m podium, the tower\'s plan and position (the roomiest part) and the colours are estimated; construction start (2017.5) is an estimate'
    },
    sources: [WIKI + 'New_Brunswick_Performing_Arts_Center', OVERTURE]
  });
}

// ---------------------------------------------------------------------- The Gateway
{
  const o = obb(GATEWAY);
  const tgt = lngLatToLocal(GATEWAY_ANCHOR, [-74.44775, 40.49741]);
  const [fx, fy] = toFrame(o, tgt[0], tgt[1]);
  NJ_TOWNS.push({
    id: 'nb_gateway',
    name: 'The Gateway',
    kind: 'tower',
    built: [2010, 2012.5],
    end: 9999,
    anchor: GATEWAY_ANCHOR,
    build: b => {
      block(b, GATEWAY, 0, 18, '#B7A99B', '#8E857B');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the tower stands over the west end beside the station (Wikipedia's coordinates)
        const [px, py, pd] = roomiest(GATEWAY, o, (qx, qy) => Math.hypot(qx - fx, qy - fy) < 22);
        const [x, y, d] = [px, py, pd];
        const [tw, tl] = fit(GATEWAY, o, x, y, Math.min(26, d * 1.3), Math.min(22, d * 1.3));
        b.color('#D2D7DA').box(x, y, 18, tw, tl, 90.83 - 18);
        b.color('#8E99A0').box(x, y, 90.5, tw, tl, 0.33);
      });
    },
    replaces: [GATEWAY],
    facts: {
      Built: 'proposed February 2005 by DEVCO (Easton-Somerset redevelopment); completed 2012; a mixed-use tower of 23 storeys beside the Northeast Corridor station, the tallest building in New Brunswick',
      Model: 'plan is the real outline of the complex (Overture, 3,952 m2); the completion year, the 23 storeys and the 298 ft (90.83 m) roof are cited; the 18 m podium, the tower\'s plan and its position (placed near Wikipedia\'s coordinates, inside the outline) are estimated; construction start (2010) is an estimate'
    },
    sources: [WIKI + 'The_Gateway_(New_Brunswick,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Kirkpatrick Chapel
{
  const o = obb(KIRKPATRICK);
  NJ_TOWNS.push({
    id: 'nb_kirkpatrick_chapel',
    name: 'Kirkpatrick Chapel',
    kind: 'building',
    built: [1872, 1873.4],
    end: 9999,
    anchor: KIRKPATRICK_ANCHOR,
    build: b => {
      block(b, KIRKPATRICK, 0, 9.1, '#7A5A48', '#3F3A38');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        b.color('#4A4541').gable(0, 0, o.W, o.L, 9.1, 7.66, true);
        // buttresses along the nave
        for (const sx of [-1, 1]) {
          for (let i = -2; i <= 2; i++) b.color('#6B4F40').box(sx * (o.W / 2 + 0.1), i * (o.L * 0.17), 0, 0.9, 1.0, 7.5);
        }
        // a pinnacle on each gable end
        for (const sy of [-1, 1]) b.color('#7A5A48').box(0, sy * (o.L / 2 - 0.4), 15.2, 0.8, 0.8, 1.5);
      });
    },
    replaces: [KIRKPATRICK],
    facts: {
      Built: 'built 1872, consecrated 1873; Henry Janeway Hardenbergh\'s High Victorian Gothic Revival chapel in brownstone, 116 ft long and 57.5 ft wide, 55 ft high; four windows from the Tiffany studios',
      Model: 'plan is the real outline (Overture, 602 m2; the cited 116 x 57.5 ft is 620 m2); the dates, material, style, the 55 ft (16.76 m) height and the dimensions are cited; the 9.1 m eave (the footprint\'s measured height), the buttresses and the pinnacles are estimated'
    },
    sources: [WIKI + 'Kirkpatrick_Chapel', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Winants Hall
{
  const o = obb(WINANTS);
  NJ_TOWNS.push({
    id: 'nb_winants_hall',
    name: 'Winants Hall',
    kind: 'building',
    built: [1888.5, 1890.5],
    end: 9999,
    anchor: WINANTS_ANCHOR,
    build: b => {
      block(b, WINANTS, 0, 13, '#9A5A44', '#4F4A46');
      b.color('#B39A82').prism(WINANTS, 12.2, 13.4, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const [hw, hl] = fit(WINANTS, o, 0, 0, o.W * 0.92, o.L * 0.94);
        b.color('#4F4A46').hip(0, 0, hw, hl, 13.4, 4.6);
        for (const sy of [-1, 1]) b.color('#7B4A38').box(0, sy * (o.L * 0.3), 13.4, 2.0, 2.0, 4.0);
      });
    },
    replaces: [WINANTS],
    facts: {
      Built: 'designed by Van Campen Taylor and completed in 1890; Rutgers College\'s first full-scale dormitory (a dormitory 1890-1947); four storeys; a contributing building of the Queens Campus historic district (National Register, 2 July 1973)',
      Model: 'plan is the real outline (Overture, 925 m2); the completion year, architect and four storeys are cited; no height is published: the 13 m walls are the footprint\'s measured height, and the hipped roof (top 18 m), the two chimneys and the string course are estimated; construction start (1888.5) is an estimate'
    },
    sources: [WIKI + 'Winants_Hall', OVERTURE]
  });
}

// ---------------------------------------------------------------------- State Theatre
{
  const o = obb(STATETHEATRE);
  NJ_TOWNS.push({
    id: 'nb_state_theatre',
    name: 'State Theatre',
    kind: 'building',
    built: [1920.5, 1921.99],
    end: 9999,
    anchor: STATETHEATRE_ANCHOR,
    build: b => {
      block(b, STATETHEATRE, 0, 15, '#C9B79A', '#8A7F70');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // lobby front at one end, the auditorium under a gable roof, the stage house at the other
        const [gw, gl] = fit(STATETHEATRE, o, 0, 0, o.W * 0.9, o.L * 0.46);
        b.color('#6F675C').gable(0, 0, gw, gl, 15, 4.2, true);
        const [sw, sl] = fit(STATETHEATRE, o, 0, -o.L * 0.33, o.W * 0.9, o.L * 0.26);
        b.color('#B6A486').box(0, -o.L * 0.33, 15, sw, sl, 8.5);
        b.color('#8A7F70').box(0, -o.L * 0.33, 23.5, sw, sl, 0.1);
        const [mw] = fit(STATETHEATRE, o, 0, o.L / 2 - 1.2, o.W * 0.55, 1.4);
        b.color('#A0452F').box(0, o.L / 2 - 0.9, 6.2, mw, 1.4, 0.4);
      });
    },
    replaces: [STATETHEATRE],
    facts: {
      Built: 'opened 26 December 1921; Thomas W. Lamb; one of the oldest theatres in New Jersey; seats 1,850; a new blade marquee in 2021',
      Model: 'plan is the real outline (Overture, 2,212 m2); the opening date, architect and seating are cited; no height is published: the 15 m walls, the auditorium roof, the 23.5 m stage house, the marquee and which end is the front are estimated; construction start (1920.5) is an estimate'
    },
    sources: [WIKI + 'State_Theatre_(New_Brunswick,_New_Jersey)', OVERTURE]
  });
}

// ---------------------------------------------------------------------- Voorhees Hall
{
  const o = obb(VOORHEES);
  NJ_TOWNS.push({
    id: 'nb_voorhees_hall',
    name: 'Voorhees Hall (Rutgers library)',
    kind: 'building',
    built: [1902, 1903.9],
    end: 9999,
    anchor: VOORHEES_ANCHOR,
    build: b => {
      block(b, VOORHEES, 0, 12, '#B4795C', '#4F4A46');
      b.color('#D2C3A8').prism(VOORHEES, 11.2, 12.4, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const [hw, hl] = fit(VOORHEES, o, 0, 0, o.W * 0.8, o.L * 0.9);
        b.color('#4F4A46').hip(0, 0, hw, hl, 12.4, 4.4);
      });
    },
    replaces: [VOORHEES],
    facts: {
      Built: '1903, built to house the Rutgers College library; named for Ralph and Elizabeth Rodman Voorhees; the library moved to Alexander Library (1956); the University Art Gallery (the Zimmerli Art Museum from 1983) was here; an addition of 2002 houses the Art History Library',
      Model: 'plan is the real outline (Overture, 2,082 m2, including the addition of 2002); the 1903 date and the use are cited; no height is published and no photograph was opened: the 12 m walls, the hipped roof (top 16.8 m) and the stone band are estimated; construction start (1902) is an estimate'
    },
    sources: [WIKI + 'Voorhees_Mall', OVERTURE]
  });
}
