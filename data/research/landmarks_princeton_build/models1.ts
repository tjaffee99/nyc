
// ====================================================================== Alexander Hall
{
  const o = obb(ALEXANDER);
  PRINCETON.push({
    id: 'pr_alexander_hall',
    name: 'Alexander Hall (Richardson Auditorium)',
    kind: 'building',
    built: [1892, 1894.45],
    end: 9999,
    anchor: ALEXANDER_ANCHOR,
    build: b => {
      block(b, ALEXANDER, 0, 13, '#8B5A45', '#5A4F49');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // great roof over the hall; ridge along the long axis
        b.color('#4F4A46').gable(0, 0, o.W * 0.7, o.L * 0.72, 13, 8, true);
        b.color('#8B5A45').box(0, 0, 13, o.W * 0.7 - 0.4, o.L * 0.72, 0.05);
        // four round corner turrets with conical caps
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) {
            const x = sx * o.W * 0.3;
            const y = sy * o.L * 0.34;
            b.color('#9A6A52').cylinder(x, y, 2.0, 0, 18, 10, {top: false});
            b.color('#4F4A46');
            spire(b, x, y, 2.3, 18, 25, 10);
          }
        }
      });
    },
    replaces: [ALEXANDER],
    facts: {
      Built: 'groundbreaking 1892, completed 1894 and opened 9 June 1894; William Appleton Potter; Richardsonian Romanesque in rusticated brownstone and red granite; 900 seats',
      Model: 'plan is the real outline (Overture, 1,136 m2); dates, style, materials and seating are cited; no height is published: the 13 m eave, the 21 m ridge and the four conical turrets (25 m) are estimated'
    },
    sources: [WIKI + 'Alexander_Hall_(Princeton_University)', WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}

// ====================================================================== East Pyne Hall
{
  const o = obb(EAST_PYNE);
  const bR = (o.bearing * Math.PI) / 180;
  const westX = -Math.cos(bR) > 0 ? 1 : -1; // sign of local +x pointing west
  PRINCETON.push({
    id: 'pr_east_pyne_hall',
    name: 'East Pyne Hall (Pyne Library)',
    kind: 'building',
    built: [1896, 1897.9],
    end: 9999,
    anchor: EAST_PYNE_ANCHOR,
    build: b => {
      block(b, EAST_PYNE, 0, 14, '#9C8F77', '#6A655C', [EAST_PYNE_H0]);
      // crenellated parapet round the outer wall
      b.color('#9C8F77').prism(EAST_PYNE, 14, 15, {top: false});
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const tx = westX * (o.W / 2 - 4.2);
        // the large tower over the western arch
        b.color('#A59A82').box(tx, 0, 14, 8.6, 8.6, 20);
        b.color('#8F846D').box(tx, 0, 34, 9.6, 9.6, 1.2);
        b.color('#A59A82').box(tx, 0, 35.2, 7.6, 7.6, 3);
        b.color('#6A655C');
        spire(b, tx, 0, 5.4, 38.2, 44, 4);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.color('#A59A82').box(tx + sx * 4.3, sy * 4.3, 34, 1.2, 1.2, 6);
        }
        // the lower, battlemented tower over the eastern arch
        const ex = -westX * (o.W / 2 - 4.2);
        b.color('#A59A82').box(ex, 0, 14, 7.2, 7.2, 9);
        b.color('#8F846D').box(ex, 0, 23, 8, 8, 1);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.box(ex + sx * 3.5, sy * 3.5, 24, 1.1, 1.1, 1.2);
        }
      });
    },
    replaces: [EAST_PYNE],
    facts: {
      Built: '1896-97 as Pyne Library, William Appleton Potter; the first explicitly Collegiate Gothic building at Princeton; the university\'s main library until 1948',
      Plan: 'a quadrangle of 216 x 155 ft (65.8 x 47.2 m) with a large tower over the western arch and a shorter, battlemented one over the eastern arch',
      Model: 'plan and courtyard are the real outline (Overture; the quadrangle size is cited and matches it); no height is published: the 14 m wall, the 44 m western tower and the 24 m eastern tower are estimated'
    },
    sources: [MUSEUM + 'artifact/252ecfae-9f12-4bf4-ae94-647a29375c32', WIKI + 'William_Appleton_Potter', OVERTURE]
  });
}

// ====================================================================== Chancellor Green
{
  const o = obb(CHANCELLOR);
  PRINCETON.push({
    id: 'pr_chancellor_green',
    name: 'Chancellor Green Library',
    kind: 'building',
    built: [1872, 1873.4],
    end: 9999,
    anchor: CHANCELLOR_ANCHOR,
    build: b => {
      block(b, CHANCELLOR, 0, 10, '#8C6B55', '#4F4A46');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the central octagon: 64 ft across, 50 ft (15.2 m) high (1905 library history)
        const r = 9.75 / Math.cos(Math.PI / 8);
        b.color('#8C6B55').prism(circle(0, 0, r, 8), 10, 15.2, {top: false});
        b.color('#4F4A46');
        b.pyramid(circle(0, 0, r + 0.4, 8), 15.2, [0, 0, 22]);
        b.color('#8C6B55').cylinder(0, 0, 1.4, 22, 24, 8);
        b.color('#4F4A46');
        spire(b, 0, 0, 1.7, 24, 27, 8);
        // pitched roofs over the two wings
        for (const s of [-1, 1]) {
          b.color('#4F4A46').gable(0, s * (o.L / 2 - 6), 10, 11, 10, 3.6, false);
        }
      });
    },
    replaces: [CHANCELLOR],
    facts: {
      Built: 'erected 1872, dedicated May 1873 as the University Library; William A. Potter; the most pronounced High Victorian Gothic building on the campus',
      Size: 'central octagon 64 ft (19.5 m) across and 50 ft (15.2 m) high; 160 ft (48.8 m) from wing to wing',
      Model: 'plan is the real outline (Overture, 661 m2; its 48 m length matches the cited 160 ft); octagon width and height are cited; the wings\' 10 m, the steep roof (22 m) and the lantern (27 m) are estimated'
    },
    sources: ['https://static-prod.lib.princeton.edu/scsites/libraryhistory/1905_Williams.html', MUSEUM, WIKI + 'Princeton_Historic_District_(Princeton,_New_Jersey)', OVERTURE]
  });
}

// ====================================================================== Holder Hall
{
  const o = obb(HOLDER);
  const [tx, ty, td] = roomiest(HOLDER, o);
  const s = Math.min(4.8, td * 0.95);
  PRINCETON.push({
    id: 'pr_holder_hall',
    name: 'Holder Hall and Holder Tower',
    kind: 'building',
    built: [1909, 1911],
    end: 9999,
    anchor: HOLDER_ANCHOR,
    build: b => {
      block(b, HOLDER, 0, 15, '#A19882', '#5F5C57');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // Holder Tower: 145 ft (44.2 m) above the campus
        b.color('#A9A08A').box(tx, ty, 15, 2 * s, 2 * s, 17);
        b.color('#928973').box(tx, ty, 32, 2 * s + 1, 2 * s + 1, 0.9);
        b.color('#A9A08A').box(tx, ty, 32.9, 2 * s - 0.8, 2 * s - 0.8, 4.5);
        b.color('#5F5C57').pyramid(rect(tx, ty, 2 * s - 0.4, 2 * s - 0.4), 37.4, [tx, ty, 44.2]);
        for (const sx of [-1, 1]) {
          for (const sy of [-1, 1]) b.color('#A9A08A').box(tx + sx * (s - 0.2), ty + sy * (s - 0.2), 32.9, 1, 1, 6);
        }
      });
    },
    replaces: [HOLDER],
    facts: {
      Built: 'commissioned 1909, the dormitory opened in 1910 and the tower was completed in 1911; Day & Klauder; Collegiate Gothic',
      Height: 'Holder Memorial Tower rises 145 ft (44.2 m) (most sources; a few say 140 ft)',
      Model: 'plan is the real outline (Overture, 1,826 m2); the tower\'s height and the dates are cited; the 15 m eave, the tower\'s plan (about 9.6 m) and where it stands (the outline\'s deepest part) are estimated'
    },
    sources: [MUSEUM + 'artifact/e6c46c30-f5d3-4757-b41d-59ea1d1c4645', 'https://dspace.njstatelib.org/items/741726e8-a7ae-41b5-ac55-2677a78c18b9', 'https://pjcarlino.blogspot.com/2008/04/holder-hall-prinecton.html', OVERTURE]
  });
}

// ====================================================================== Firestone Library
{
  const o = obb(FIRESTONE);
  PRINCETON.push({
    id: 'pr_firestone_library',
    name: 'Firestone Library',
    kind: 'building',
    built: [1946.5, 1948.5],
    end: 9999,
    anchor: FIRESTONE_ANCHOR,
    build: b => {
      block(b, FIRESTONE, 0, 14.5, '#B1A78F', '#6A675F');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // slate roof: a hip over the deepest part of the plan, and a pitched entrance bay
        const [hx, hy, hd] = roomiest(FIRESTONE, o);
        const s = Math.min(hd * 0.95, 22);
        b.color('#5C5A57').hip(hx, hy, 2 * s, 2 * s, 14.5, 3.2);
        b.color('#B8AE96').box(hx, hy - s - 1, 0, 12, 2, 16.5);
        b.color('#5C5A57').gable(hx, hy - s - 1, 12.4, 2.2, 16.5, 2.2, false);
      });
    },
    replaces: [FIRESTONE],
    facts: {
      Built: 'opened 1948 (extended 1971 and 1988); Robert B. O\'Connor and Walter H. Kilham Jr.; Collegiate Gothic; four floors above ground and three partly below',
      Model: 'plan is the real outline (Overture, 8,526 m2, which includes the later extensions); the opening year and the four floors are cited; the 14.5 m eave, the hip roof and the entrance bay are estimated; construction start (1946) is an estimate'
    },
    sources: [WIKI + 'Firestone_Library', OVERTURE]
  });
}

// ====================================================================== Robertson Hall
{
  const o = obb(ROBERTSON);
  PRINCETON.push({
    id: 'pr_robertson_hall',
    name: 'Robertson Hall',
    kind: 'building',
    built: [1963.5, 1966.4],
    end: 9999,
    anchor: ROBERTSON_ANCHOR,
    build: b => {
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        const wd = o.W;
        const ln = o.L;
        const set = 3.6;
        // ground floor, 28 ft (8.5 m) high, set back inside the colonnade
        b.color('#CFC7B2').box(0, 0, 0, wd - 2 * set, ln - 2 * set, 8.5);
        // the upper floor and flat roof on the full outline
        b.color('#E7E3D6').box(0, 0, 8.5, wd, ln, 4.2);
        b.color('#D8D3C4').box(0, 0, 12.7, wd + 0.4, ln + 0.4, 0.3);
        // 58 tapered white columns round the perimeter
        const per = 2 * (wd + ln);
        const step = per / 58;
        for (let i = 0; i < 58; i++) {
          let t = i * step;
          let x = 0;
          let y = 0;
          if (t < ln) {
            x = -wd / 2 + 0.4;
            y = -ln / 2 + t;
          } else if ((t -= ln) < wd) {
            x = -wd / 2 + t;
            y = ln / 2 - 0.4;
          } else if ((t -= wd) < ln) {
            x = wd / 2 - 0.4;
            y = ln / 2 - t;
          } else {
            t -= ln;
            x = wd / 2 - t;
            y = -ln / 2 + 0.4;
          }
          b.color('#F3F1EA').loft([rect(x, y, 0.5, 0.5), rect(x, y, 0.9, 0.9)], [0, 12.7], {top: false});
        }
      });
    },
    replaces: [ROBERTSON],
    facts: {
      Built: 'gift of 1961, dedicated May 1966; Minoru Yamasaki, for the Woodrow Wilson School',
      Design: 'three levels (one below ground); 58 tapered white quartz-faced columns carry the top floor over a ground storey 28 ft (8.5 m) high with non-bearing travertine walls; reflecting pool on the plaza',
      Model: 'plan is the real outline (Overture, 2,096 m2); the column count and the 28 ft ground storey are cited; the 4.2 m upper floor (12.7 m top), the 3.6 m setback of the ground storey and the column taper are estimated; construction start (1963.5) is an estimate'
    },
    sources: [MUSEUM + 'artifact/432444fe-2157-4704-92f6-a6d54d8ef1f1', OVERTURE]
  });
}

// ====================================================================== Lewis Library
{
  const o = obb(LEWIS);
  const [tx, ty, td] = roomiest(LEWIS, o);
  const s = Math.min(6.5, td * 0.95);
  PRINCETON.push({
    id: 'pr_lewis_library',
    name: 'Lewis Library (Frank Gehry)',
    kind: 'building',
    built: [2006, 2008.7],
    end: 9999,
    anchor: LEWIS_ANCHOR,
    build: b => {
      block(b, LEWIS, 0, 9.5, '#8F5F49', '#B4B9BC');
      b.frame(o.cx, o.cy, 0, o.bearing, () => {
        // the tower: 105 ft (32.0 m) to the parapet; brick below, stainless-steel lid above
        b.color('#8F5F49').box(tx, ty, 9.5, 2 * s, 2 * s, 18);
        b.color('#B4B9BC').loft([rect(tx, ty, 2 * s, 2 * s), rect(tx, ty, 2 * s - 2.6, 2 * s - 2.6)], [27.5, 32.004]);
      });
    },
    replaces: [LEWIS],
    facts: {
      Opened: '11 September 2008; Frank Gehry; brick and stainless steel; 87,000 gross sq ft; four storeys in the tower, three in the Ivy Lane wing, two in the Washington Road wing',
      Height: 'highest point 105 ft (32.0 m), from grade to the top of the parapet coping (the university\'s fact sheet; earlier coverage said 103 ft)',
      Model: 'plan is the real outline (Overture, 2,463 m2); the 32.0 m top is cited; the wings\' height (9.5 m), the tower\'s plan and place (the outline\'s deepest part) and the steel lid are estimated; construction start (2006) is an estimate'
    },
    sources: ['https://www.princeton.edu/news/2008/09/03/lewis-library-fact-sheet', OVERTURE]
  });
}
