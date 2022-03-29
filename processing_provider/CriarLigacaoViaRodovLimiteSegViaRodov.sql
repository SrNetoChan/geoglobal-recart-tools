/* Criar copias das tabelas originais e passar pelo snap */
UPDATE TEMP.CONNECTION_road SET
	geom = ST_SnapToGrid(geom, 0.001);

DROP TABLE IF EXISTS TEMP.seg_via_rodov;
CREATE TABLE TEMP.seg_via_rodov AS table seg_via_rodov;

UPDATE TEMP.seg_via_rodov SET
	geometria = ST_SnapToGrid(geometria, 0.001);

CREATE INDEX ON TEMP.seg_via_rodov USING gist(geometria);

DROP TABLE IF EXISTS TEMP.via_rodov_limite;
CREATE TABLE TEMP.via_rodov_limite AS table via_rodov_limite;

UPDATE TEMP.via_rodov_limite SET
	geometria = ST_SnapToGrid(geometria, 0.001);

CREATE INDEX ON TEMP.via_rodov_limite USING gist(geometria);


/* Unir todas as linhas e cortar nos nós */
DROP TABLE IF EXISTS TEMP.noded_lines;

WITH all_lines AS (
SELECT st_force2d((st_dump(geom)).geom) AS geom FROM TEMP.CONNECTION_road
UNION ALL
SELECT ST_SnapToGrid(st_force2d(geometria), 0.001) AS geom FROM TEMP.seg_via_rodov
UNION ALL
SELECT ST_SnapToGrid(st_force2d(geometria), 0.001) AS geom FROM TEMP.via_rodov_limite)
SELECT st_node(st_collect(geom)) AS tipo 
INTO TEMP.noded_lines
FROM ALL_lines
WHERE ST_Length(geom) > 0;


/* correr polygonize para criar poligonos entre as linhas */
DROP TABLE IF EXISTS TEMP.ALL_polygons;
SELECT (st_dump(st_polygonize(tipo))).geom AS geom
INTO TEMP.ALL_polygons
FROM TEMP.noded_lines;

CREATE INDEX ON TEMP.ALL_polygons USING gist(geom);

/* Estabelecer ligacao entre as geometria do segviarodov e o viarodovlimite
   usando os poligonos que tocam ambos */

DROP TABLE IF EXISTS TEMP.lig_segviarodov_viarodovlimite;
SELECT 
	ROW_NUMBER() OVER () AS id,
	svr.identificador AS seg_via_rodov_id
	, apol.geom::geometry(polygon,5016)
	, vrl.identificador AS via_rodov_limite_id
INTO TEMP.lig_segviarodov_viarodovlimite
FROM 
	TEMP.seg_via_rodov svr
	JOIN TEMP.ALL_polygons AS apol ON st_relate(apol.geom, svr.geometria,'***1*****')
	JOIN TEMP.via_rodov_limite vrl ON st_relate(apol.geom, vrl.geometria,'***1*****')
WHERE
	NOT svr.valor_tipo_troco_rodoviario IN ('6','7') 
	AND apol.geom && svr.geometria
	AND apol.geom && vrl.geometria;

CREATE INDEX ON TEMP.lig_segviarodov_viarodovlimite USING gist(geom);
CREATE INDEX ON TEMP.lig_segviarodov_viarodovlimite(via_rodov_limite_id);

DROP TABLE IF EXISTS TEMP.limites_nao_ligados;
SELECT * 
INTO TEMP.limites_nao_ligados
FROM via_rodov_limite vrl
WHERE NOT EXISTS (SELECT 1 FROM temp.lig_segviarodov_viarodovlimite WHERE via_rodov_limite_id = vrl.identificador);

CREATE INDEX ON TEMP.limites_nao_ligados USING gist(geometria);

/* Limpar tabelas temporárias */
DROP TABLE IF EXISTS TEMP.noded_lines;
DROP TABLE IF EXISTS TEMP.ALL_polygons;