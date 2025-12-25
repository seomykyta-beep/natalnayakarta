class NatalChart {
    constructor(elementId, size) {
        this.container = document.getElementById(elementId);
        this.size = size;
        this.cx = size / 2;
        this.cy = size / 2;
        this.ns = "http://www.w3.org/2000/svg";
        
        this.isMobile = size < 400;

        // Более воздушные радиусы
        this.rOuter = size / 2 - 5;
        this.rOuterAccent = this.rOuter - (this.isMobile ? 8 : 18);
        this.rZodiacOuter = this.rOuterAccent - (this.isMobile ? 4 : 8);
        this.rZodiacInner = this.rZodiacOuter - (this.isMobile ? 28 : 42);
        this.rPlanetBase = this.rZodiacInner - (this.isMobile ? 15 : 22);
        this.rAspect = this.rPlanetBase - (this.isMobile ? 40 : 60);
        this.rHouseText = this.rAspect - (this.isMobile ? 12 : 18);
        this.rInner = this.rAspect - (this.isMobile ? 25 : 40);

        // Для двойной карты
        this.rTransitOuter = this.rOuter - (this.isMobile ? 6 : 12);
        this.rTransitInner = this.rTransitOuter - (this.isMobile ? 30 : 48);
        
        this.svg = document.createElementNS(this.ns, "svg");
        this.svg.setAttribute("width", size);
        this.svg.setAttribute("height", size);
        this.svg.style.display = "block";
        this.container.innerHTML = "";
        this.container.appendChild(this.svg);

        // Добавляем градиенты
        this.addDefs();

        this.signs = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"];
        
        // Пастельные цвета стихий: Огонь/Земля/Воздух/Вода
        this.signColors = [
            "rgba(255,120,100,0.25)", "rgba(139,195,74,0.25)", "rgba(255,235,59,0.25)", "rgba(100,181,246,0.25)",
            "rgba(255,120,100,0.25)", "rgba(139,195,74,0.25)", "rgba(255,235,59,0.25)", "rgba(100,181,246,0.25)",
            "rgba(255,120,100,0.25)", "rgba(139,195,74,0.25)", "rgba(255,235,59,0.25)", "rgba(100,181,246,0.25)"
        ];
        
        this.glyphColors = {
            Sun: "#ff8f00", Moon: "#546e7a", Mercury: "#8d6e63", Venus: "#66bb6a",
            Mars: "#ef5350", Jupiter: "#42a5f5", Saturn: "#78909c",
            Uranus: "#26c6da", Neptune: "#7e57c2", Pluto: "#ab47bc",
            North_node: "#607d8b", South_node: "#607d8b", Lilith: "#455a64",
            Chiron: "#9c27b0", ASC: "#e91e63", MC: "#3f51b5"
        };
        this.planetIcons = {
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
            North_node: "☊", South_node: "☋", Lilith: "⚸", Chiron: "⚷",
            ASC: "AC", MC: "MC"
        };
    }

    addDefs() {
        const defs = document.createElementNS(this.ns, "defs");
        
        // Градиент для фона
        const bgGrad = document.createElementNS(this.ns, "radialGradient");
        bgGrad.id = "bgGradient";
        bgGrad.innerHTML = '<stop offset="0%" stop-color="#fafafa"/><stop offset="100%" stop-color="#e8e8e8"/>';
        defs.appendChild(bgGrad);
        
        // Градиент для внутреннего круга
        const innerGrad = document.createElementNS(this.ns, "radialGradient");
        innerGrad.id = "innerGradient";
        innerGrad.innerHTML = '<stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#f5f5f5"/>';
        defs.appendChild(innerGrad);
        
        // Градиент для транзитного кольца
        const transitGrad = document.createElementNS(this.ns, "radialGradient");
        transitGrad.id = "transitGradient";
        transitGrad.innerHTML = '<stop offset="0%" stop-color="#e3f2fd"/><stop offset="100%" stop-color="#bbdefb"/>';
        defs.appendChild(transitGrad);
        
        // Тень
        const shadow = document.createElementNS(this.ns, "filter");
        shadow.id = "shadow";
        shadow.innerHTML = '<feDropShadow dx="0" dy="1" stdDeviation="2" flood-opacity="0.15"/>';
        defs.appendChild(shadow);
        
        this.svg.appendChild(defs);
    }

    setAttr(el, name, value) {
        if (el) el.setAttribute(name, value);
    }

    draw(data) {
        if (!data || !data.houses || data.houses.length < 12) return;
        this.svg.innerHTML = "";
        this.addDefs();
        this.rotationOffset = 180 - (data.houses[0] || 0);
        
        const hasOuter = data.outerPlanets && data.outerPlanets.length > 0;
        if (hasOuter) {
            this.drawDualChart(data);
        } else {
            this.drawSingleChart(data);
        }
    }

    drawSingleChart(data) {
        this.drawBackground();
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawCenterCircle();
    }

    drawDualChart(data) {
        const s = this.size;
        const m = this.isMobile;
        
        // Пересчёт радиусов для двойной карты
        this.rOuter = s / 2 - 5;
        this.rTransitOuter = this.rOuter - (m ? 5 : 10);
        this.rTransitInner = this.rTransitOuter - (m ? 32 : 50);
        this.rZodiacOuter = this.rTransitInner - (m ? 5 : 10);
        this.rZodiacInner = this.rZodiacOuter - (m ? 24 : 36);
        this.rPlanetBase = this.rZodiacInner - (m ? 12 : 18);
        this.rAspect = this.rPlanetBase - (m ? 30 : 50);
        this.rHouseText = this.rAspect - (m ? 10 : 15);
        this.rInner = this.rAspect - (m ? 20 : 35);

        this.drawDualBackground();
        this.drawTransitRing(data.outerPlanets);
        this.drawZodiacRing();
        this.drawHouses(data.houses);
        if (data.aspects) this.drawAspects(data.aspects, data.planets);
        if (data.planets) this.drawPlanets(data.planets);
        this.drawCenterCircle();
    }

    drawBackground() {
        // Внешний круг с градиентом
        const outer = document.createElementNS(this.ns, "circle");
        this.setAttr(outer, "cx", this.cx);
        this.setAttr(outer, "cy", this.cy);
        this.setAttr(outer, "r", this.rOuter);
        this.setAttr(outer, "fill", "url(#bgGradient)");
        this.setAttr(outer, "filter", "url(#shadow)");
        this.svg.appendChild(outer);

        // Внутренний белый круг
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, "cx", this.cx);
        this.setAttr(inner, "cy", this.cy);
        this.setAttr(inner, "r", this.rZodiacInner);
        this.setAttr(inner, "fill", "url(#innerGradient)");
        this.svg.appendChild(inner);
    }

    drawDualBackground() {
        // Внешний круг
        const outer = document.createElementNS(this.ns, "circle");
        this.setAttr(outer, "cx", this.cx);
        this.setAttr(outer, "cy", this.cy);
        this.setAttr(outer, "r", this.rOuter);
        this.setAttr(outer, "fill", "url(#transitGradient)");
        this.setAttr(outer, "filter", "url(#shadow)");
        this.svg.appendChild(outer);

        // Разделительная линия между транзитами и натальной картой
        const divider = document.createElementNS(this.ns, "circle");
        this.setAttr(divider, "cx", this.cx);
        this.setAttr(divider, "cy", this.cy);
        this.setAttr(divider, "r", this.rTransitInner);
        this.setAttr(divider, "fill", "none");
        this.setAttr(divider, "stroke", "#90caf9");
        this.setAttr(divider, "stroke-width", "2");
        this.svg.appendChild(divider);

        // Белый фон под зодиаком
        const zodiacBg = document.createElementNS(this.ns, "circle");
        this.setAttr(zodiacBg, "cx", this.cx);
        this.setAttr(zodiacBg, "cy", this.cy);
        this.setAttr(zodiacBg, "r", this.rZodiacOuter);
        this.setAttr(zodiacBg, "fill", "#fafafa");
        this.svg.appendChild(zodiacBg);

        // Центральный белый круг
        const inner = document.createElementNS(this.ns, "circle");
        this.setAttr(inner, "cx", this.cx);
        this.setAttr(inner, "cy", this.cy);
        this.setAttr(inner, "r", this.rZodiacInner);
        this.setAttr(inner, "fill", "url(#innerGradient)");
        this.svg.appendChild(inner);
    }

    drawTransitRing(planets) {
        if (!planets) return;
        
        const used = [];
        planets.forEach(p => {
            if (p.abs_pos === undefined && p.abs_pos !== 0) return;
            let angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            let r = (this.rTransitOuter + this.rTransitInner) / 2;

            // Антиколлизия
            for (let u of used) {
                const diff = Math.abs(angle - u.angle);
                if (diff < 0.18 || diff > Math.PI * 2 - 0.18) {
                    r -= this.isMobile ? 12 : 16;
                }
            }
            used.push({ angle, r });

            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            // Подсветка планеты
            const glow = document.createElementNS(this.ns, "circle");
            this.setAttr(glow, "cx", x);
            this.setAttr(glow, "cy", y);
            this.setAttr(glow, "r", this.isMobile ? 8 : 11);
            this.setAttr(glow, "fill", "rgba(33,150,243,0.15)");
            this.svg.appendChild(glow);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", x);
            this.setAttr(text, "y", y);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", this.isMobile ? "11" : "14");
            this.setAttr(text, "font-weight", "600");
            this.setAttr(text, "fill", "#1976d2");
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);
        });
    }

    drawZodiacRing() {
        // Внешняя граница зодиака
        const outerBorder = document.createElementNS(this.ns, "circle");
        this.setAttr(outerBorder, "cx", this.cx);
        this.setAttr(outerBorder, "cy", this.cy);
        this.setAttr(outerBorder, "r", this.rZodiacOuter);
        this.setAttr(outerBorder, "fill", "none");
        this.setAttr(outerBorder, "stroke", "#bdbdbd");
        this.setAttr(outerBorder, "stroke-width", "1");
        this.svg.appendChild(outerBorder);

        for (let i = 0; i < 12; i++) {
            const startAngle = (i * 30 + this.rotationOffset) * Math.PI / 180;
            const endAngle = ((i + 1) * 30 + this.rotationOffset) * Math.PI / 180;
            
            // Сегмент зодиака
            const path = document.createElementNS(this.ns, "path");
            const x1 = this.cx + this.rZodiacOuter * Math.cos(startAngle);
            const y1 = this.cy + this.rZodiacOuter * Math.sin(startAngle);
            const x2 = this.cx + this.rZodiacOuter * Math.cos(endAngle);
            const y2 = this.cy + this.rZodiacOuter * Math.sin(endAngle);
            const x3 = this.cx + this.rZodiacInner * Math.cos(endAngle);
            const y3 = this.cy + this.rZodiacInner * Math.sin(endAngle);
            const x4 = this.cx + this.rZodiacInner * Math.cos(startAngle);
            const y4 = this.cy + this.rZodiacInner * Math.sin(startAngle);
            
            const d = `M${x1},${y1} A${this.rZodiacOuter},${this.rZodiacOuter} 0 0,1 ${x2},${y2} L${x3},${y3} A${this.rZodiacInner},${this.rZodiacInner} 0 0,0 ${x4},${y4} Z`;
            this.setAttr(path, "d", d);
            this.setAttr(path, "fill", this.signColors[i]);
            this.setAttr(path, "stroke", "#e0e0e0");
            this.setAttr(path, "stroke-width", "0.5");
            this.svg.appendChild(path);

            // Символ знака
            const midAngle = ((i + 0.5) * 30 + this.rotationOffset) * Math.PI / 180;
            const rMid = (this.rZodiacOuter + this.rZodiacInner) / 2;
            const tx = this.cx + rMid * Math.cos(midAngle);
            const ty = this.cy + rMid * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", tx);
            this.setAttr(text, "y", ty);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", this.isMobile ? "13" : "18");
            this.setAttr(text, "fill", "#424242");
            text.textContent = this.signs[i];
            this.svg.appendChild(text);
        }

        // Внутренняя граница зодиака
        const innerBorder = document.createElementNS(this.ns, "circle");
        this.setAttr(innerBorder, "cx", this.cx);
        this.setAttr(innerBorder, "cy", this.cy);
        this.setAttr(innerBorder, "r", this.rZodiacInner);
        this.setAttr(innerBorder, "fill", "none");
        this.setAttr(innerBorder, "stroke", "#bdbdbd");
        this.setAttr(innerBorder, "stroke-width", "1.5");
        this.svg.appendChild(innerBorder);
    }

    drawHouses(houses) {
        for (let i = 0; i < 12; i++) {
            const angle = (houses[i] + this.rotationOffset) * Math.PI / 180;
            const x1 = this.cx + this.rZodiacInner * Math.cos(angle);
            const y1 = this.cy + this.rZodiacInner * Math.sin(angle);
            const x2 = this.cx + (this.rInner + 5) * Math.cos(angle);
            const y2 = this.cy + (this.rInner + 5) * Math.sin(angle);
            
            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, "x1", x1);
            this.setAttr(line, "y1", y1);
            this.setAttr(line, "x2", x2);
            this.setAttr(line, "y2", y2);
            
            // Угловые дома (1,4,7,10) толще
            const isAngular = i % 3 === 0;
            this.setAttr(line, "stroke", isAngular ? "#616161" : "#bdbdbd");
            this.setAttr(line, "stroke-width", isAngular ? "2" : "1");
            this.svg.appendChild(line);

            // Номер дома
            const nextHouse = houses[(i + 1) % 12];
            let midAngle = (houses[i] + nextHouse) / 2;
            if (nextHouse < houses[i]) midAngle = (houses[i] + nextHouse + 360) / 2;
            midAngle = (midAngle + this.rotationOffset) * Math.PI / 180;
            
            const tx = this.cx + this.rHouseText * Math.cos(midAngle);
            const ty = this.cy + this.rHouseText * Math.sin(midAngle);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", tx);
            this.setAttr(text, "y", ty);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", this.isMobile ? "9" : "11");
            this.setAttr(text, "fill", "#757575");
            this.setAttr(text, "font-weight", "500");
            text.textContent = (i + 1).toString();
            this.svg.appendChild(text);
        }
    }

    drawPlanets(planets) {
        const used = [];
        planets.forEach(p => {
            if (p.abs_pos === undefined && p.abs_pos !== 0) return;
            let angle = (p.abs_pos + this.rotationOffset) * Math.PI / 180;
            let r = this.rPlanetBase;

            // Антиколлизия
            for (let u of used) {
                const diff = Math.abs(angle - u.angle);
                if (diff < 0.18 || diff > Math.PI * 2 - 0.18) {
                    r -= this.isMobile ? 14 : 20;
                }
            }
            used.push({ angle, r });

            const x = this.cx + r * Math.cos(angle);
            const y = this.cy + r * Math.sin(angle);
            
            // Подсветка планеты
            const glow = document.createElementNS(this.ns, "circle");
            this.setAttr(glow, "cx", x);
            this.setAttr(glow, "cy", y);
            this.setAttr(glow, "r", this.isMobile ? 9 : 12);
            this.setAttr(glow, "fill", "rgba(255,255,255,0.8)");
            this.svg.appendChild(glow);
            
            const text = document.createElementNS(this.ns, "text");
            this.setAttr(text, "x", x);
            this.setAttr(text, "y", y);
            this.setAttr(text, "text-anchor", "middle");
            this.setAttr(text, "dominant-baseline", "central");
            this.setAttr(text, "font-size", this.isMobile ? "12" : "16");
            this.setAttr(text, "font-weight", "bold");
            this.setAttr(text, "fill", this.glyphColors[p.key] || "#424242");
            text.textContent = this.planetIcons[p.key] || p.icon || "●";
            this.svg.appendChild(text);
        });
    }

    drawAspects(aspects, planets) {
        const posMap = {};
        planets.forEach(p => {
            if (p.abs_pos !== undefined) posMap[p.key] = p.abs_pos;
            if (p.name) posMap[p.name] = p.abs_pos;
        });

        const colors = {
            Conjunction: "#64b5f6", Sextile: "#81c784", Square: "#e57373",
            Trine: "#aed581", Opposition: "#ffb74d", Quincunx: "#4dd0e1"
        };

        aspects.forEach(a => {
            const pos1 = posMap[a.p1_key] ?? posMap[a.p1];
            const pos2 = posMap[a.p2_key] ?? posMap[a.p2];
            if (pos1 === undefined || pos2 === undefined) return;

            const angle1 = (pos1 + this.rotationOffset) * Math.PI / 180;
            const angle2 = (pos2 + this.rotationOffset) * Math.PI / 180;
            const r = this.rInner + 5;
            
            const x1 = this.cx + r * Math.cos(angle1);
            const y1 = this.cy + r * Math.sin(angle1);
            const x2 = this.cx + r * Math.cos(angle2);
            const y2 = this.cy + r * Math.sin(angle2);

            const line = document.createElementNS(this.ns, "line");
            this.setAttr(line, "x1", x1);
            this.setAttr(line, "y1", y1);
            this.setAttr(line, "x2", x2);
            this.setAttr(line, "y2", y2);
            this.setAttr(line, "stroke", colors[a.type] || "#e0e0e0");
            this.setAttr(line, "stroke-width", "1");
            this.setAttr(line, "opacity", "0.5");
            this.svg.appendChild(line);
        });
    }

    drawCenterCircle() {
        // Центральный декоративный круг
        const center = document.createElementNS(this.ns, "circle");
        this.setAttr(center, "cx", this.cx);
        this.setAttr(center, "cy", this.cy);
        this.setAttr(center, "r", this.rInner);
        this.setAttr(center, "fill", "none");
        this.setAttr(center, "stroke", "#e0e0e0");
        this.setAttr(center, "stroke-width", "1");
        this.svg.appendChild(center);
        
        // Маленький центральный круг
        const innerCenter = document.createElementNS(this.ns, "circle");
        this.setAttr(innerCenter, "cx", this.cx);
        this.setAttr(innerCenter, "cy", this.cy);
        this.setAttr(innerCenter, "r", this.isMobile ? 8 : 12);
        this.setAttr(innerCenter, "fill", "#fafafa");
        this.setAttr(innerCenter, "stroke", "#bdbdbd");
        this.setAttr(innerCenter, "stroke-width", "1");
        this.svg.appendChild(innerCenter);
    }
}
