/*-- Cria vertices 3D na intersecção com curvas de nível */

/*-- Fazer backup das tabelas originais */

CREATE SCHEMA IF NOT EXISTS backup;

CREATE TABLE backup.via_rodov_limite_bk (like public.via_rodov_limite INCLUDING DEFAULTS);

INSERT INTO backup.via_rodov_limite_bk
SELECT * FROM public.via_rodov_limite;

CREATE TABLE backup.curva_de_nivel_bk (like public.curva_de_nivel INCLUDING DEFAULTS);

INSERT INTO backup.curva_de_nivel_bk
SELECT * FROM public.curva_de_nivel;

/* Criar indices espaciais para melhorar a performance */

CREATE INDEX IF NOT EXISTS via_rodov_limite_geometria_idx ON via_rodov_limite USING gist(geometria);
CREATE INDEX IF NOT EXISTS curva_de_nivel_geometria_idx ON curva_de_nivel USING gist(geometria);

/* Criar tabela com pontos de intersecção entre as camadas para fazer snapping às camadas originais */

CREATE SCHEMA IF NOT EXISTS temp;

DROP TABLE temp.snap_points;
CREATE TABLE temp.snap_points as
SELECT vrl.identificador, 
	cdn.identificador AS cdn_identificador, 
	st_translate(
		st_force3d(
			st_force2d(
				(st_dumppoints(ST_intersection(vrl.geometria,cdn.geometria))).geom))
		,0,	0,st_z(st_startpoint(cdn.geometria))
		) AS geometria
FROM via_rodov_limite vrl 
	JOIN curva_de_nivel cdn ON st_intersects(vrl.geometria,cdn.geometria)
	LEFT JOIN lig_segviarodov_viarodovlimite lsl on (lsl.via_rodov_limite_id = vrl.identificador)
	LEFT JOIN seg_via_rodov svr ON (lsl.seg_via_rodov_id = svr.identificador)
WHERE svr.valor_posicao_vertical_transportes = '0' OR svr.valor_posicao_vertical_transportes IS NULL;

CREATE INDEX ON temp.snap_points(identificador);
CREATE INDEX ON temp.snap_points(cdn_identificador);

/* Fazer snap das geometrias originais às intersecções entre as duas camadas */

WITH points_collect AS (
	SELECT identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY identificador
	)
UPDATE via_rodov_limite AS vrlt SET
geometria = st_snap(vrlt.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE vrlt.identificador = sc.identificador;

WITH points_collect AS (
	SELECT cdn_identificador, st_collect(geometria) AS geometria
	FROM temp.snap_points 
	GROUP BY cdn_identificador
	)
UPDATE curva_de_nivel AS cdnt SET
geometria = st_snap(cdnt.geometria, sc.geometria, 0.01)
FROM points_collect AS sc
WHERE cdnt.identificador = sc.cdn_identificador;
