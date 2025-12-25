class NatalChart {
    constructor(elementId, size) {
        this.container = document.getElementById(elementId);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
        this.ns = "http://www.w3.org/2000/svg";
        this.isMobile = size < 400;

        this.svg = document.createElementNS(this.ns, "svg");
        this.svg.setAttribute("width", size);
        this.svg.setAttribute("height", size);
        this.svg.setAttribute("viewBox", "0 0 " + size + " " + size);
        this.container.innerHTML = "";
        this.container.appendChild(this.svg);

        this.signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
        
        // Цвета знаков по стихиям (как у Geocult)
        this.signColors = [
            "#c62828", "#4e342e", "#2e7d32", "#1565c0",  // Овен,Телец,Близнецы,Рак
            "#c62828", "#4e342e", "#2e7d32", "#1565c0",  // Лев,Дева,Весы,Скорпион
            "#c62828", "#4e342e", "#2e7d32", "#1565c0"   // Стрелец,Козерог,Водолей,Рыбы
        ];
        
        this.planetColors = {
            Sun: "#ff6f00", Moon: "#5d4037", Mercury: "#795548", Venus: "#2e7d32",
            Mars: "#c62828", Jupiter: "#1565c0", Saturn: "#37474f",
            Uranus: "#00838f", Neptune: "#4527a0", Pluto: "#6a1b9a",
            North_node: "#455a64", South_node: "#455a64", Lilith: "#c62828",
            Chiron: "#6a1b9a", ASC: "#1565c0", MC: "#1565c0"
        };
        
        this.planetSymbols = {
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
            North_node: "☊", South_node: "☋", Lilith: "⚸", Chiron: "⚷",
            ASC: "AC", MC: "MC"
        };
    }

    attr(el, a) { for(let k in a) el.setAttribute(k, a[k]); return el; }
    circle(cx, cy, r, fill, stroke, sw) {
        const c = document.createElementNS(this.ns, "circle");
        return this.attr(c, {cx, cy, r, fill: fill||"none", stroke: stroke||"none", "stroke-width": sw||1});
    }
    line(x1, y1, x2, y2, stroke, sw) {
        const l = document.createElementNS(this.ns, "line");
        return this.attr(l, {x1, y1, x2, y2, stroke, "stroke-width": sw||1});
    }
    text(x, y, txt, size, fill, anchor, weight) {
        const t = document.createElementNS(this.ns, "text");
        this.attr(t, {x, y, "text-anchor": anchor||"middle", "dominant-baseline": "central", 
            "font-size": size, "font-family": "Arial, sans-serif", fill: fill||"#000", "font-weight": weight||"normal"});
        t.textContent = txt;
        return t;
    }

    draw(data) {
        if (!data || !data.houses || data.houses.length < 12) return;
        this.svg.innerHTML = "";
        this.rot = 180 - (data.houses[0] || 0);
        this.houses = data.houses;
        
        const hasTransit = data.outerPlanets && data.outerPlanets.length > 0;
        const s = this.size, m = this.isMobile;
        
        // Радиусы как у Geocult
        if (hasTransit) {
            this.R = s/2 - 2;                              // внешний край
            this.rTransitO = this.R;                       // транзитное кольцо внешнее
            this.rTransitI = this.R - (m ? 38 : 60);       // транзитное кольцо внутреннее
            this.rTickO = this.rTransitI;                  // риски внешние
            this.rTickI = this.rTransitI - (m ? 14 : 22);  // риски внутренние
            this.rSignO = this.rTickI;                     // знаки внешние
            this.rSignI = this.rSignO - (m ? 30 : 48);     // знаки внутренние
            this.rPlanetO = this.rSignI;                   // натальные планеты внешние
            this.rPlanetI = this.rPlanetO - (m ? 28 : 44); // натальные планеты внутренние
            this.rHouseO = this.rPlanetI;                  // дома внешние
            this.rCenter = this.rHouseO - (m ? 20 : 32);   // центральный круг
        } else {
            this.R = s/2 - 2;
            this.rTickO = this.R;
            this.rTickI = this.R - (m ? 14 : 22);
            this.rSignO = this.rTickI;
            this.rSignI = this.rSignO - (m ? 35 : 55);
            this.rPlanetO = this.rSignI;
            this.rPlanetI = this.rPlanetO - (m ? 32 : 50);
            this.rHouseO = this.rPlanetI;
            this.rCenter = this.rHouseO - (m ? 22 : 35);
        }

        // Рисуем слои
        if (hasTransit) this.drawTransitRing(data.outerPlanets);
        this.drawTicksRing();
        this.drawZodiacRing();
        this.drawHouseSectors();
        this.drawNatalPlanets(data.planets);
        this.drawHouseLines();
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        this.drawCenterCircles();
        this.drawHouseNumbers();
        this.drawAxisLabels();
    }

    // Зелёное транзитное кольцо
    drawTransitRing(planets) {
        // Градиентный зелёный фон
        const defs = document.createElementNS(this.ns, "defs");
        const grad = document.createElementNS(this.ns, "radialGradient");
        grad.id = "greenGrad";
        grad.innerHTML = '<stop offset="0%" stop-color="#c8e6c9"/><stop offset="100%" stop-color="#a5d6a7"/>';
        defs.appendChild(grad);
        this.svg.appendChild(defs);

        // Внешний зелёный круг
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rTransitO, "url(#greenGrad)", "#81c784", 1));
        
        // Белый внутренний круг (граница транзитного кольца)
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rTransitI, "#fff", "#9e9e9e", 1));

        // Транзитные планеты
        const used = [];
        (planets || []).forEach(p => {
            if (p.abs_pos === undefined) return;
            const ang = (p.abs_pos + this.rot) * Math.PI / 180;
            let r = (this.rTransitO + this.rTransitI) / 2;
            
            for (let u of used) {
                if (Math.abs(ang - u.a) < 0.15 || Math.abs(ang - u.a) > 6.13) r -= this.isMobile ? 11 : 15;
            }
            used.push({a: ang, r});
            
            const x = this.cx + r * Math.cos(ang);
            const y = this.cy + r * Math.sin(ang);
            
            this.svg.appendChild(this.text(x, y, this.planetSymbols[p.key] || "●", 
                this.isMobile ? 12 : 16, "#37474f", "middle", "bold"));
            
            if (p.is_retro) {
                this.svg.appendChild(this.text(x + (this.isMobile?8:11), y - (this.isMobile?6:9), 
                    "R", this.isMobile ? 7 : 9, "#c62828", "middle", "bold"));
            }
        });
    }

    // Красные риски градусов
    drawTicksRing() {
        // Белый фон под риски
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rTickO, "#fff", "#bdbdbd", 1));
        
        for (let d = 0; d < 360; d++) {
            const ang = (d + this.rot) * Math.PI / 180;
            const isBig = d % 5 === 0;
            const len = isBig ? (this.isMobile ? 8 : 12) : (this.isMobile ? 4 : 6);
            
            const x1 = this.cx + this.rTickO * Math.cos(ang);
            const y1 = this.cy + this.rTickO * Math.sin(ang);
            const x2 = this.cx + (this.rTickO - len) * Math.cos(ang);
            const y2 = this.cy + (this.rTickO - len) * Math.sin(ang);
            
            this.svg.appendChild(this.line(x1, y1, x2, y2, "#c62828", isBig ? 1.2 : 0.6));
        }
    }

    // Знаки зодиака (просто символы на белом фоне!)
    drawZodiacRing() {
        // Белый фон
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rSignO, "#fff", "#bdbdbd", 1));
        
        // Разделительные линии между знаками (только в кольце!)
        for (let i = 0; i < 12; i++) {
            const ang = (i * 30 + this.rot) * Math.PI / 180;
            const x1 = this.cx + this.rSignO * Math.cos(ang);
            const y1 = this.cy + this.rSignO * Math.sin(ang);
            const x2 = this.cx + this.rSignI * Math.cos(ang);
            const y2 = this.cy + this.rSignI * Math.sin(ang);
            this.svg.appendChild(this.line(x1, y1, x2, y2, "#bdbdbd", 1));
        }

        // Символы знаков (большие цветные)
        for (let i = 0; i < 12; i++) {
            const ang = ((i + 0.5) * 30 + this.rot) * Math.PI / 180;
            const r = (this.rSignO + this.rSignI) / 2;
            const x = this.cx + r * Math.cos(ang);
            const y = this.cy + r * Math.sin(ang);
            
            this.svg.appendChild(this.text(x, y, this.signs[i], 
                this.isMobile ? 18 : 28, this.signColors[i], "middle", "bold"));
        }

        // Внутренняя граница
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rSignI, "#fff", "#9e9e9e", 1.5));
    }

    // Секторы домов (светло-серый фон)
    drawHouseSectors() {
        for (let i = 0; i < 12; i++) {
            const start = (this.houses[i] + this.rot) * Math.PI / 180;
            const end = (this.houses[(i+1)%12] + this.rot) * Math.PI / 180;
            
            // Чередующийся серый фон
            const fill = i % 2 === 0 ? "#f5f5f5" : "#fff";
            
            const path = document.createElementNS(this.ns, "path");
            const x1 = this.cx + this.rPlanetO * Math.cos(start);
            const y1 = this.cy + this.rPlanetO * Math.sin(start);
            const x2 = this.cx + this.rPlanetO * Math.cos(end);
            const y2 = this.cy + this.rPlanetO * Math.sin(end);
            const x3 = this.cx + this.rCenter * Math.cos(end);
            const y3 = this.cy + this.rCenter * Math.sin(end);
            const x4 = this.cx + this.rCenter * Math.cos(start);
            const y4 = this.cy + this.rCenter * Math.sin(start);
            
            // Определяем большую дугу
            let sweep = end - start;
            if (sweep < 0) sweep += Math.PI * 2;
            const largeArc = sweep > Math.PI ? 1 : 0;
            
            const d = "M" + x1 + "," + y1 + 
                      " A" + this.rPlanetO + "," + this.rPlanetO + " 0 " + largeArc + ",1 " + x2 + "," + y2 +
                      " L" + x3 + "," + y3 +
                      " A" + this.rCenter + "," + this.rCenter + " 0 " + largeArc + ",0 " + x4 + "," + y4 + " Z";
            
            this.attr(path, {d, fill, stroke: "none"});
            this.svg.appendChild(path);
        }
    }

    // Натальные планеты (цветные символы)
    drawNatalPlanets(planets) {
        const used = [];
        (planets || []).forEach(p => {
            if (p.abs_pos === undefined) return;
            const ang = (p.abs_pos + this.rot) * Math.PI / 180;
            let r = (this.rPlanetO + this.rPlanetI) / 2;
            
            for (let u of used) {
                if (Math.abs(ang - u.a) < 0.18 || Math.abs(ang - u.a) > 6.10) r -= this.isMobile ? 13 : 18;
            }
            used.push({a: ang, r});
            
            const x = this.cx + r * Math.cos(ang);
            const y = this.cy + r * Math.sin(ang);
            
            this.svg.appendChild(this.text(x, y, this.planetSymbols[p.key] || "●", 
                this.isMobile ? 14 : 18, this.planetColors[p.key] || "#424242", "middle", "bold"));
            
            if (p.is_retro) {
                this.svg.appendChild(this.text(x + (this.isMobile?9:12), y - (this.isMobile?7:10), 
                    "R", this.isMobile ? 8 : 10, "#c62828", "middle", "bold"));
            }
        });
    }

    // Линии домов
    drawHouseLines() {
        for (let i = 0; i < 12; i++) {
            const ang = (this.houses[i] + this.rot) * Math.PI / 180;
            const isAngular = i % 3 === 0;
            
            const x1 = this.cx + this.rPlanetO * Math.cos(ang);
            const y1 = this.cy + this.rPlanetO * Math.sin(ang);
            const x2 = this.cx + this.rCenter * Math.cos(ang);
            const y2 = this.cy + this.rCenter * Math.sin(ang);
            
            this.svg.appendChild(this.line(x1, y1, x2, y2, isAngular ? "#424242" : "#9e9e9e", isAngular ? 2 : 1));
        }
    }

    // Аспекты (цветные линии)
    drawAspects(aspects, planets) {
        const pos = {};
        (planets || []).forEach(p => {
            if (p.abs_pos !== undefined) {
                pos[p.key] = p.abs_pos;
                if (p.name) pos[p.name] = p.abs_pos;
            }
        });

        const colors = {
            Conjunction: "#42a5f5", Sextile: "#66bb6a", Square: "#e53935",
            Trine: "#43a047", Opposition: "#c62828", Quincunx: "#26c6da"
        };

        (aspects || []).forEach(a => {
            const p1 = pos[a.p1_key] ?? pos[a.p1];
            const p2 = pos[a.p2_key] ?? pos[a.p2];
            if (p1 === undefined || p2 === undefined) return;

            const a1 = (p1 + this.rot) * Math.PI / 180;
            const a2 = (p2 + this.rot) * Math.PI / 180;
            const r = this.rCenter - 3;
            
            const orb = Math.abs(a.orb || 0);
            const w = orb < 1 ? 2 : orb < 3 ? 1.5 : 1;
            
            this.svg.appendChild(this.line(
                this.cx + r * Math.cos(a1), this.cy + r * Math.sin(a1),
                this.cx + r * Math.cos(a2), this.cy + r * Math.sin(a2),
                colors[a.type] || "#bdbdbd", w
            ));
        });
    }

    // Двойной центральный круг
    drawCenterCircles() {
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rCenter, "none", "#616161", 1.5));
        this.svg.appendChild(this.circle(this.cx, this.cy, this.rCenter - (this.isMobile?5:8), "none", "#9e9e9e", 1));
    }

    // Номера домов
    drawHouseNumbers() {
        for (let i = 0; i < 12; i++) {
            let mid = (this.houses[i] + this.houses[(i+1)%12]) / 2;
            if (this.houses[(i+1)%12] < this.houses[i]) mid = (this.houses[i] + this.houses[(i+1)%12] + 360) / 2;
            const ang = (mid + this.rot) * Math.PI / 180;
            const r = this.rCenter - (this.isMobile ? 15 : 22);
            
            this.svg.appendChild(this.text(
                this.cx + r * Math.cos(ang), this.cy + r * Math.sin(ang),
                (i+1).toString(), this.isMobile ? 9 : 12, "#616161", "middle", "normal"
            ));
        }
    }

    // Подписи осей AC/DC/MC/IC снаружи карты
    drawAxisLabels() {
        const m = this.isMobile;
        const axes = [
            {h: 0, lbl: "AC", arrow: true},
            {h: 6, lbl: "DC"},
            {h: 9, lbl: "MC"},
            {h: 3, lbl: "IC"}
        ];

        axes.forEach(ax => {
            const ang = (this.houses[ax.h] + this.rot) * Math.PI / 180;
            const r = this.R + (m ? 14 : 22);
            const x = this.cx + r * Math.cos(ang);
            const y = this.cy + r * Math.sin(ang);
            
            this.svg.appendChild(this.text(x, y, ax.lbl, m ? 11 : 15, "#1565c0", "middle", "bold"));
            
            // Синяя стрелка для AC
            if (ax.arrow) {
                const len = m ? 20 : 30;
                const ax1 = this.cx + this.R * Math.cos(ang);
                const ay1 = this.cy + this.R * Math.sin(ang);
                const ax2 = ax1 - len * Math.cos(ang);
                const ay2 = ay1 - len * Math.sin(ang);
                this.svg.appendChild(this.line(ax1, ay1, ax2, ay2, "#1565c0", 2));
                
                // Наконечник стрелки
                const arrowSize = m ? 5 : 8;
                const perpAng = ang + Math.PI/2;
                const tipX = ax2;
                const tipY = ay2;
                const baseX1 = ax2 + arrowSize * Math.cos(ang) + arrowSize/2 * Math.cos(perpAng);
                const baseY1 = ay2 + arrowSize * Math.sin(ang) + arrowSize/2 * Math.sin(perpAng);
                const baseX2 = ax2 + arrowSize * Math.cos(ang) - arrowSize/2 * Math.cos(perpAng);
                const baseY2 = ay2 + arrowSize * Math.sin(ang) - arrowSize/2 * Math.sin(perpAng);
                
                const arrow = document.createElementNS(this.ns, "polygon");
                this.attr(arrow, {points: tipX+","+tipY+" "+baseX1+","+baseY1+" "+baseX2+","+baseY2, fill: "#1565c0"});
                this.svg.appendChild(arrow);
            }
        });
    }
}
